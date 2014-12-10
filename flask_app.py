import re
from urllib.error import HTTPError
from flask import Flask, jsonify, make_response, request, current_app
from datetime import datetime, timedelta
from functools import update_wrapper

from patent_helper import GooglePatent
from patentapi import GooglePatentPublication

from flask import request, render_template

# CORS decorator
def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


app = Flask(__name__)

@app.route('/')
def index():
    #return 'Running Patent API Server v.0.0.1!'
    return render_template("index.html")


@app.route('/patent', methods=['POST'])
def patent():
    pub_num = request.get_json()
    #print('\n\n' + post_data + '\n\n')
    #pub_num = post_data.get('publication_number')
    #print(pub_num);

    return get_publication(pub_num)


@app.errorhandler(404)
def not_found(num=None):
    message = 'Not Found - ' + str(num)
    myJSON = {'status': 404, 'message': message}
    resp = jsonify(myJSON)
    resp.status_code = 200

    return resp

@app.route('/api/test/patents/<string:pub_num>', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*')
def get_publication(pub_num):
    #print('\n\n' + pub_num + '\n\n')
    #print('API WAS ACCESSED AT ' + str(datetime.now()))

    regex = re.compile('US[\d]{1,15}', re.IGNORECASE)
    if regex.match(pub_num):

        try:
            pat = GooglePatentPublication(pub_num)
            pat.dict['message'] = 'OK'
            pat.dict['status'] = 200
            return jsonify(pat.dict)
        except Exception as err:
            #raise err
            pass
            return not_found(pub_num)

    return not_found(pub_num)

if __name__ == '__main__':
    app.run(debug=True)
