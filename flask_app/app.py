from flask import Flask, render_template, request, redirect, url_for, session, flash
import base64
import json
import requests
import os

from flask_cognito_lib import CognitoAuth
from flask_cognito_lib.decorators import (
    auth_required,
    cognito_login,
    cognito_login_callback,
    cognito_logout,
    cognito_refresh_callback,
)
from flask_cognito_lib.exceptions import (
    AuthorisationRequiredError,
    CognitoGroupRequiredError,
)
secret_key = os.urandom(24)
app = Flask(__name__)
app.secret_key = str(secret_key)

# Configuration required for CognitoAuth
app.config["AWS_REGION"] = "us-east-1"
app.config["AWS_COGNITO_USER_POOL_ID"] = "us-east-1_16xwSaIul"
app.config["AWS_COGNITO_DOMAIN"] = "https://pixtag38.auth.us-east-1.amazoncognito.com"
app.config["AWS_COGNITO_USER_POOL_CLIENT_ID"] = "9jhjt7qirggh9snla7b07ukqk"
app.config["AWS_COGNITO_REDIRECT_URL"] = "https://pixtag.vercel.app/postlogin"
app.config["AWS_COGNITO_LOGOUT_URL"] = "https://pixtag.vercel.app"
app.config["AWS_COGNITO_REFRESH_FLOW_ENABLED"] = True
app.config["AWS_COGNITO_REFRESH_COOKIE_ENCRYPTED"] = True
app.config["AWS_COGNITO_REFRESH_COOKIE_AGE_SECONDS"] = 86400
auth = CognitoAuth(app)


@app.route('/')
@cognito_login
def index():
    # return render_template('index.html')
    session['state'] = "true"
    return redirect("https://pixtag38.auth.us-east-1.amazoncognito.com/login?client_id=9jhjt7qirggh9snla7b07ukqk&response_type=code&scope=openid+profile&redirect_uri=https%3A%2F%2Fpixtag.vercel.app%2F")

@app.route("/postlogin")
@cognito_login_callback
def postlogin():
    return redirect(url_for("index_redirect"))

@app.route("/refresh", methods=["POST"])
@cognito_refresh_callback
def refresh():
    pass

@app.route('/home', methods=['GET', 'POST'])
@auth_required()
def index_redirect():
    return render_template("index.html")

@app.route('/upload', methods=['GET', 'POST'])
@auth_required()
def upload_image():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_name = file.filename
            try:
                image_data = base64.b64encode(file.read()).decode('utf-8')
                upload_api_endpoint = "https://bf9tbiuk94.execute-api.us-east-1.amazonaws.com/raw/api/upload"
                headers = {
                    'Content-Type': 'application/json'
                }
                payload = {
                    'body': json.dumps({
                        'image': image_data,
                        'file_name': file_name
                    })
                }
                response = requests.post(upload_api_endpoint, json=payload, headers=headers)
                response_data = response.json()

                if response.status_code == 200:
                    flash(f"Image {file_name} uploaded successfully!", "success")
                else:
                    flash(f"Failed to upload image {file_name}. Response: {response.text}", "danger")
            except Exception as e:
                flash(str(e), "danger")
    return render_template('upload.html')

@app.route('/searchthumbnail', methods=['GET', 'POST'])
@auth_required()
def search_thumbnail():
    if request.method == 'POST':
        thumbnail_url = request.form['thumbnail_url']
        payload = {
            "url" : thumbnail_url
        }
        headers = {
            'Content-Type': 'application/json'
        }
        search_api_endpoint = "https://8c4hmrvb44.execute-api.us-east-1.amazonaws.com/prod/api/thumbnail"
        try:
            response = requests.post(search_api_endpoint, json=payload, headers=headers)
            response_data = response.json()
            print(response)
            print(response_data.get('body'))
            if response.status_code == 200:
                flash(f"Full Size Raw Image URL: {response_data}", "success")
            else:
                flash(f"Image Not Found: {response_data}","failure")
        except Exception as e:
            flash(str(e), "danger")
    return render_template('search_thumbnail.html')

@app.route('/delete', methods=['GET', 'POST'])
@auth_required()
def delete_images():
    images = []
    try:
        list_image_endpoint = "https://e9jy13yplf.execute-api.us-east-1.amazonaws.com/prod/api/url"
        response = requests.get(list_image_endpoint)
        response_data = response.json()
        if response.status_code == 200:
            images = response_data.get('images', [])
        else:
            flash(f"Failed to fetch images: {response_data.get('message')}", "danger")
    except Exception as e:
        flash(str(e), "danger")

    if request.method == 'POST':
        urls_to_delete = request.form['urls'].split(',')
        payload = {
            "httpMethod": "POST",
            "body": json.dumps({
                "image_urls": [url.strip() for url in urls_to_delete]
            })
        }
        headers = {
            'Content-Type': 'application/json'
        }
        delete_api_endpoint = "https://e9jy13yplf.execute-api.us-east-1.amazonaws.com/prod/api/url"
        try:
            response = requests.post(delete_api_endpoint, json=payload, headers=headers)
            response_data = response.json()
            print(response_data)
            if response_data.get('statusCode') == 200:
                deleted_images = response_data.get('deleted_images', [])
                failed_images = response_data.get('failed_images', [])
                message = f"Deleted Images:\n{', '.join(urls_to_delete)}"
                if failed_images:
                    message += f"\nFailed to Delete:\n{', '.join(failed_images)}"
                flash(message, "success")
            else:
                flash(f"Failed to delete images: {response_data.get('message')}", "danger")
        except Exception as e:
            flash(str(e), "danger")
    return render_template('delete.html', images=images)
@app.route('/edit', methods=['GET', 'POST'])
@auth_required()
def edit_tags():
    try:
        get_all_data = "https://6afpoe4d5a.execute-api.us-east-1.amazonaws.com/prod/api/get_thumb"
        response = requests.get(get_all_data)
        response_data = response.json()

        if 'items' in response_data:
            items = response_data['items']
        else:
            items = []

    except Exception as e:
        print(f"Error fetching thumbnail data: {e}")
        items = []

    if request.method == 'POST':
        # Process form submission
        url = request.form.get('url')
        operation_type = int(request.form.get('type', 1))  # Default to 1 (add tags)
        tags = request.form.get('tags')
        payload = {
            "url":[url],
            "type": operation_type,
            "tags":[tag.strip() for tag in tags.split(",")]
        }
        edit_tags_url = "https://qxu6w13n62.execute-api.us-east-1.amazonaws.com/prod/api/edit_tags"
        try:
            response = requests.post(edit_tags_url,json=payload)
            response_data = response.json()
            if response.status_code == 200:
                print(f"Updated Details: {response_data}")
            else:
                print("Failed to process")
        except Exception as e:
            print("Failed")
        return redirect(url_for('edit_tags'))  # Redirect to refresh the page after processing

    return render_template('edit.html', items=items)
@app.route('/find', methods = ['GET','POST'])
@auth_required()
def get_image_tag():
    if request.method == 'POST':
        tags = request.form.get('tags')
        if not tags:
            flash("Tags are required", "danger")
            return redirect(url_for('get_image_tag'))

        tags_list = [tag.strip() for tag in tags.split(",")]

        payload = {
            "httpMethod": "POST",
            "body": json.dumps({
                "tags": tags_list
            })
        }
        headers = {
            'Content-Type': 'application/json'
        }
        find_api_endpoint = "https://wsavwhghef.execute-api.us-east-1.amazonaws.com/prod/api/get_tag"
        try:
            response = requests.post(find_api_endpoint, json=payload, headers=headers)
            response_data = response.json()
            if response_data.get('statusCode') == 200:
                #flash(f"Matching Image URLs:\n{', '.join(image_links)}", "success")
                body = response_data['body']
                #links = body.get('links',[])
                flash(f"Matching Image URLs:\n{body}", "success")
            else:
                flash(f"Failed to find images: {response_data.get('message')}", "danger")
        except Exception as e:
            flash(str(e), "danger")
    return render_template('find.html')
@app.route('/query', methods=['GET', 'POST'])
@auth_required()
def query_image_tags():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if file:
                # Read file contents and encode to base64
                image_data = base64.b64encode(file.read()).decode('utf-8')
                payload = {
                    "body": image_data
                }
                headers = {
                    'Content-Type': 'application/json'
                }
                lambda_endpoint = "https://7ktizee099.execute-api.us-east-1.amazonaws.com/prod/api/extract"  # Replace with your Lambda endpoint
                response = requests.post(lambda_endpoint, json=payload, headers=headers)
                response_data = response.json()
                if response.status_code == 200:
                    response_data = json.loads(response.text)
                    matching_urls = response_data.get('matching_urls', [])
                    tags = response_data.get('tags', [])
                    if len(matching_urls) > 0:
                        return render_template('query.html', matching_urls=matching_urls, tags=tags)
                    else:
                        flash("No Images with the Tags found","success")
                        return render_template('query.html', matching_urls=matching_urls, tags=tags)
                else:
                    flash(f"Failed to process image. Response: {response.text}", "danger")
            else:
                flash("No file uploaded", "danger")
        except Exception as e:
            flash(str(e), "danger")

    return render_template('query.html')

@app.route("/logout")
@cognito_logout
def logout():
    session.clear()  # Clear Flask session
    response = redirect("/")  # Redirect to home or login page
    return response
if __name__ == '__main__':
    app.run(debug=True)
