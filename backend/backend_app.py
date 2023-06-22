"""
Backend API endpoints for Blog Posts
"""
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
    returns: posts list (json)
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
def add_post() -> tuple[Response, int]:
    """
    An API endpoint to add a new blog post
    """
    new_post = request.get_json()

    if not validate_post_data(new_post):
        return jsonify({"error": "Invalid Post Data"}), 400  # bad request

    add_new_post(new_post)

    return jsonify(new_post), 201  # Created


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
