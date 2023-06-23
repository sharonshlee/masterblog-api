"""
Blog Application RESTful API Web Service.
A RESTful API with Flask that implement
listing, adding, deleting, updating,
searching, and sorting blog posts.
Implemented endpoints,
errors handling,
pagination,
rate limit,
logging and
testing API with Postman.
"""
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

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
    {"id": 3, "title": "Third post", "content": "This is the third post."},
    {"id": 4, "title": "Fourth post", "content": "This is the fourth post."},
    {"id": 5, "title": "Fifth post", "content": "This is the fifth post."},
    {"id": 6, "title": "Sixth post", "content": "This is the sixth post."},
    {"id": 7, "title": "Seventh post", "content": "This is the seventh post."},
    {"id": 8, "title": "Eighth post", "content": "This is the eighth post."},
    {"id": 9, "title": "Ninth post", "content": "This is the ninth post."},
    {"id": 10, "title": "Tenth post", "content": "This is the tenth post."},
]


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
        limit = int(request.args.get('limit', 10))
    except ValueError:
        return bad_request_error('')

    start_index = (page - 1) * limit
    end_index = start_index + limit

    return start_index, end_index


def sort_posts() -> bool | List | None:
    """
    Sort blog posts by title or content,
    in ascending or descending order.
    sort: Specifies the field (title or content) by which
          posts should be sorted.
    direction: Specifies the sort order (asc or desc).
    returns:
        bad request error message, 400 (Tuple[Response, int])
        sorted posts (List) or
        None
    """
    # /api/posts?sort=title&direction=desc
    sort = request.args.get('sort')
    direction = request.args.get('direction', 'asc')

    if sort is not None:
        if sort not in ['title', 'content'] or \
                direction not in ['asc', 'desc']:
            return False

        sorted_posts = sorted(POSTS, key=lambda post: post[sort], reverse=direction == 'desc')
        return sorted_posts
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

    sorted_posts = sort_posts()
    if sorted_posts is not None:
        if not sorted_posts:
            return bad_request_error('')
        return jsonify(sorted_posts[start_index:end_index])

    return jsonify(POSTS[start_index:end_index])


def validate_post_data(new_post: dict) -> bool:
    """
    Return True if new post data
    has title and content
    otherwise return False
    param new_data: dict
    returns: True | False (bool)
    """
    return ('title' in new_post and 'content' in new_post) and \
        new_post['title'] != '' and new_post['content'] != ''


def generate_new_id() -> int:
    """
    Generate a new unique identifier
    for new post
    returns:
        a new unique post id (int)
    """
    return max(post['id'] for post in POSTS) + 1


def add_new_post(new_post: dict):
    """
    Update the new_post with new id and
    append it the POSTS list
    param new_post: dict
    """
    new_id = 1

    if POSTS:
        # generate a new id for the post
        new_id = generate_new_id()

    new_post.update({"id": new_id})
    POSTS.append(new_post)


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

    add_new_post(new_post)

    return jsonify(new_post), 201  # Created


def find_post_by_id(post_id: int) -> dict | None:
    """
    Find the post with the given id
    param post_id: int
    returns:
        Post (dict)
        None
    """
    for post in POSTS:
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

    post = find_post_by_id(post_id)

    if post is None:
        return not_found_error('')

    POSTS.remove(post)
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

    post = find_post_by_id(post_id)

    if post is None:
        return not_found_error('')

    new_post = request.get_json()

    if new_post != {}:
        if not validate_post_data_update(new_post):
            return bad_request_error('')

    post.update(new_post)

    return jsonify(post), 200  # Ok


@app.route('/api/posts/search', methods=['GET'])
def search_post() -> List[dict]:
    """
    An API endpoint that will allow clients
    to search for posts by their
    title or content.
    returns:
        empty list or
        searched result (List[dict])
    """
    app.logger.info('GET request received for /api/posts/search')

    # url = "/api/posts/search?title=flask"
    # url = "/api/posts/search?content=python"

    title = request.args.get('title')
    content = request.args.get('content')

    search_result = []
    for post in POSTS:
        if title is not None and \
                title.strip().lower() in post['title'].lower():
            search_result.append(post)

        if content is not None and \
                content.strip().lower() in post['content'].lower():
            search_result.append(post)

    return search_result


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
