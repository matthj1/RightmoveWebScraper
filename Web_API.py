from flask import Flask, jsonify
from flask_restful import Api, Resource, reqparse
from Scraper_Class import RightMoveScrapper
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor() as executor:

    app = Flask(__name__)
    api = Api(app)

    BASE = "http://127.0.0.1:5000/" # Our base URI

    next_task_id = 0


    def generate_id():
        global next_task_id
        this_task = next_task_id
        next_task_id += 1
        return this_task


    object_dictionary = {}
    returns_dictionary = {}

    new_search_args = reqparse.RequestParser()
    new_search_args.add_argument("search_area", type=str)
    new_search_args.add_argument("max_bedrooms", type=int)
    new_search_args.add_argument("min_bedrooms", type=int)
    new_search_args.add_argument("max_price", type=int)
    new_search_args.add_argument("min_price", type=int)
    new_search_args.add_argument("show_house_type", action="append")
    new_search_args.add_argument("must_have", action="append")
    new_search_args.add_argument("dont_show", action="append")


    class NewSearch(Resource):
        def put(self):
            args = new_search_args.parse_args()
            search_id = generate_id()
            search_accepted = {"ID": search_id, "URI_Pending": BASE + "pending/" + str(search_id)}
            object_dictionary[search_id] = RightMoveScrapper(**args)
            returns_dictionary[search_id] = executor.submit(object_dictionary[search_id].scrape)
            return search_accepted, 202


    class CheckStatus(Resource):
        def get(self, search_id):
            if search_id in returns_dictionary:
                if returns_dictionary[search_id].running():
                    return "Search in progress", 400
                if returns_dictionary[search_id].done():
                    search_complete = {"ID": search_id, "URI_Complete": BASE + "completed/" + str(search_id)}
                    return search_complete, 400


    class ReturnResults(Resource):
        def get(self, search_id):
            return returns_dictionary[search_id].result()


    api.add_resource(NewSearch, "/")
    api.add_resource(CheckStatus, "/pending/<int:search_id>")
    api.add_resource(ReturnResults, "/completed/<int:search_id>")

    if __name__ == '__main__':
        app.run(debug=True)
