"""
Backend API endpoints for Blog Posts
"""
from typing import Tuple
from flask import Flask, jsonify, request, Response
# pip3 install flask-cors
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]


@app.route('/api/posts', methods=['GET'])
def get_posts() -> Response:
    """
    A GET API endpoint for
    listing all the posts
    in the storage
    returns: posts list (Response)
    """
    return jsonify(POSTS)


def validate_post_data(new_post: dict):
    """
    Return True if new post data
    has title and content
    otherwise return False
    param new_data: dict
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
    new_post = request.get_json()

    if not validate_post_data(new_post):
        return jsonify({"error": "Invalid Post Data"}), 400  # bad request

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
    post = find_post_by_id(post_id)

    if post is None:
        return Response(''), 404  # Not Found

    POSTS.remove(post)
    message = {"message": f"Post with id {post_id} has been deleted successfully."}
    return jsonify(message), 200  # 204 No Content


@app.errorhandler(404)
def not_found_error():
    """
    Handle 404, Not Found Error
    returns:
        Not Found error message, 404 (Tuple[Response, int])
    """
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(405)
def method_not_allowed_error() -> Tuple[Response, int]:
    """
    Handle 405, Method Not Allowed Error
    returns:
        Method Not Allowed error message, 405 (Tuple[Response, int])
    """
    return jsonify({"error": "Method Not Allowed"}), 405


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
