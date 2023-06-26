"""
Blog Application Web Service.

A RESTful API using Flask that
implements listing, adding, deleting,
updating, searching, and sorting blog posts.

Implemented CORS endpoints, error handling,
pagination, rate limit, and logging features.
Testing API with Postman.
"""
from datetime import datetime
import json
import logging
from typing import Tuple, List
from flask import Flask, jsonify, request, Response
# pip3 install flask-cors
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

limiter = Limiter(app)
limiter.key_func = get_remote_address

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

FILE_PATH = 'static/posts.json'


def read_file():
    """
    Reading from a JSON file
    """
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None


def write_file(blog_posts):
    """
    Writing to JSON file
    """
    with open(FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(blog_posts, file)


def pagination() -> tuple[Response, int] | tuple[int, int]:
    """
    Implement pagination for listing blog posts
    with page and limit parameters
    returns:
        bad request error message, 400 (tuple[Response, int])
        start and end index for the page (tuple[int, int])
    """
    try:
        # /api/posts?page=2&limit=5
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
    except ValueError:
        return bad_request_error('')

    start_index = (page - 1) * limit
    end_index = start_index + limit

    return start_index, end_index


def sort_posts(posts: List[dict]) -> bool | List | None:
    """
    Sort blog posts by title, content, author or date,
    in ascending or descending order.
    sort: Specifies the field by which
          posts should be sorted.
    direction: Specifies the sort order (asc or desc).
    Params:
        posts: List[dict]
    Returns:
        False if sort or direction is not
            the desired parameters (bool)
        sorted posts (List) or
        None
    """
    # /api/posts?sort=title&direction=desc
    sort = request.args.get('sort')
    direction = request.args.get('direction', 'asc')

    if sort is not None:
        if sort not in ['title', 'content', 'author', 'date'] or \
                direction not in ['asc', 'desc']:
            return False

        if sort == 'date':
            return sorted(posts,
                          key=lambda post: datetime.strptime(post[sort], "%Y-%m-%d").date(),
                          reverse=direction == 'desc')

        return sorted(posts,
                      key=lambda post: post[sort],
                      reverse=direction == 'desc')
    return None


@app.route('/api/posts', methods=['GET'])
@limiter.limit("10/minute")  # Limit to 10 requests per minute, not apply to localhost
def get_posts() -> Tuple[Response, int] | Response:
    """
    A GET API endpoint for
    listing all the posts with pagination.
    It also allows the posts
    to be sorted by title or content,
    in ascending or descending order.
    returns:
        posts list (Response) or
        ordered posts list (Response) or
        bad request error message, 400 (tuple[Response, int])
    """
    app.logger.info('GET request received for /api/posts')

    start_index, end_index = pagination()

    posts = read_file()

    if posts is None:
        return not_found_error('')

    sorted_posts = sort_posts(posts)
    if sorted_posts is not None:
        if not sorted_posts:
            return bad_request_error('')
        return jsonify(sorted_posts[start_index:end_index])

    return jsonify(posts[start_index:end_index])


def validate_post_data(new_post: dict) -> bool:
    """
    Return True if new post data
    has title and content
    otherwise return False
    Params:
        new_data: dict
    Returns:
        True | False (bool)
    """
    return ('title' in new_post and 'content' in new_post) and \
        new_post['title'] != '' and new_post['content'] != ''


def generate_new_id(posts: List[dict]) -> int:
    """
    Generate a new unique identifier
    for new post
    Params:
        posts: List[dict]
    Returns:
        a new unique post id (int)
    """
    return max(post['id'] for post in posts) + 1


def add_new_post(posts: List[dict], new_post: dict):
    """
    Update the new_post with new id and
    append it the posts list
    Params:
        posts: List[dict]
        new_post: dict
    """
    new_id = 1

    if posts:
        # generate a new id for the post
        new_id = generate_new_id(posts)

    new_post.update({"id": new_id})
    posts.append(new_post)
    write_file(posts)


@app.route('/api/posts', methods=['POST'])
def add_post() -> Tuple[Response, int]:
    """
    An API endpoint to add a new blog post
    returns:
        Invalid post data error message, bad request status code
        New post, created status code
    """
    app.logger.info('POST request received for /api/posts')

    new_post = request.get_json()

    if not validate_post_data(new_post):
        return bad_request_error('')

    posts = read_file()

    if posts is None:
        return not_found_error('')

    add_new_post(posts, new_post)

    return jsonify(new_post), 201  # Created


def find_post_by_id(posts: List[dict], post_id: int) -> dict | None:
    """
    Find the post with the given id
    param post_id: int
    returns:
        Post (dict)
        None
    """
    for post in posts:
        if post['id'] == post_id:
            return post
    return None


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id: int) -> Tuple[Response, int]:
    """
    An API endpoint to delete a post by its id
    **An OPTIONS request to the server is made
    before DELETE, PUT, PATCH methods
    to obtain permission or "preflight" the request.
    CORS helps ensure that only trusted sources are able
    to make cross-origin requests and
    helps protect against potential security vulnerabilities.
    params post_id: int
    returns:
        Delete message, 200 (Tuple[Response, int])
        Empty message, 404 (Tuple[Response, int])
    """
    app.logger.info('DELETE request received for /api/posts/%s', post_id)

    posts = read_file()

    if posts is None:
        return not_found_error('')

    post = find_post_by_id(posts, post_id)

    posts.remove(post)
    write_file(posts)
    message = {"message": f"Post with id {post_id} has been deleted successfully."}
    return jsonify(message), 200  # OK


def validate_post_data_update(new_post) -> bool:
    """
    Return True if the key
    of the new post data
    is title or content
    otherwise return False
    param new_post: dict
    returns: True | False (bool)
    """
    for key in new_post:
        if key in ['title', 'content']:
            return True
    return False


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id: int) -> Tuple[Response, int]:
    """
    An API endpoint to update an existing blog post
    returns:
        not found error message or
        bad request error message or
        the updated post, 200 (Tuple[Response, int])
    """
    app.logger.info('PUT request received for /api/posts/%s', post_id)

    posts = read_file()
    if posts is None:
        return not_found_error('')

    post = find_post_by_id(posts, post_id)

    new_post = request.get_json()

    if new_post != {}:
        if not validate_post_data_update(new_post):
            return bad_request_error('')

    post.update(new_post)
    write_file(posts)

    return jsonify(post), 200  # Ok


def get_search_term() -> tuple[str, str] | None:
    """
    Get search term from
    request url parameters
    returns:
        dict key, search term (str)
        None
    """
    # url = "/api/posts/search?title=flask"
    title = request.args.get('title')
    content = request.args.get('content')
    author = request.args.get('author')
    date = request.args.get('date')

    if title is not None:
        return 'title', title
    if content is not None:
        return 'content', content
    if author is not None:
        return 'author', author
    if date is not None:
        return 'date', date
    return None


@app.route('/api/posts/search', methods=['GET'])
def search_post() -> Tuple[Response, int] | List[dict]:
    """
    An API endpoint that will allow clients
    to search for posts by their
    title or content.
    Returns:
        not found error message, 404 (Tuple[Response, int])
        empty list (List) or
        searched result (List[dict])
    """
    app.logger.info('GET request received for /api/posts/search')

    posts = read_file()

    if posts is None:
        return not_found_error('')

    if get_search_term() is None:
        return bad_request_error('')

    key, search_term = get_search_term()

    search_result = []
    for post in posts:
        if search_term.strip().lower() in post[key].lower():
            search_result.append(post)

    return jsonify(search_result)


@app.errorhandler(404)
def not_found_error(_error) -> Tuple[Response, int]:
    """
    Handle 404, Not Found Error
    returns:
        Post Not Found error message, 404 (Tuple[Response, int])
    """
    return jsonify({"error": "Post Not Found"}), 404


@app.errorhandler(405)
def method_not_allowed_error(_error) -> Tuple[Response, int]:
    """
    Handle 405, Method Not Allowed Error
    returns:
        Method Not Allowed error message, 405 (Tuple[Response, int])
    """
    return jsonify({"error": "Method Not Allowed"}), 405


@app.errorhandler(400)
def bad_request_error(_error) -> Tuple[Response, int]:
    """
    Handle 400, Bad Request Error
    returns:
        Bad Request error message, 400 (Tuple[Response, int])
    """
    return jsonify({"error": "Invalid Post Data"}), 400


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
