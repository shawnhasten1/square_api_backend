from flask import Flask, json, jsonify, request, session
from flask_cors import CORS

import uuid
from square.client import Client
import os

app = Flask(__name__)
CORS(app)
app.secret_key = '2abceVR5ENE7FgMxXdMwuzUJKC2g8xgy'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

app.config['client'] = Client(
    access_token=os.environ['SQUARE_ACCESS_TOKEN'],
    environment='sandbox')


@app.route('/v1/categories', methods=['GET', 'POST'])
def getCategories():
    if request.method == 'GET':
        result = app.config['client'].catalog.list_catalog(
            types = "CATEGORY"
        )
        req = []
        for category in result.body['objects']:
            req.append({
                'version':category['version'],
                'id':category['id'],
                'name':category['category_data']['name']
            })
        return jsonify(req)
    elif request.method == 'POST':
        idempotency_key = uuid.uuid4()
        result = app.config['client'].catalog.upsert_catalog_object(
            body = {
                "idempotency_key": str(idempotency_key),
                "object": {
                    "type": "CATEGORY",
                    "id":"#1",
                    "category_data": {
                        "name": request.json['name']
                    }
                }
            }
        )
        return jsonify(result.body)

@app.route('/v1/categories/<cat_id>', methods=['GET', 'PUT', 'DELETE'])
def categories(cat_id):
    if request.method == 'GET':
        result = app.config['client'].catalog.retrieve_catalog_object(
            object_id = cat_id
        )
        return jsonify(result.body['object'])
    elif request.method == 'PUT':
        idempotency_key = uuid.uuid4()
        result = app.config['client'].catalog.retrieve_catalog_object(
            object_id = cat_id
        )
        version_id = result.body['object']['version']
        result = app.config['client'].catalog.batch_upsert_catalog_objects(
            body = {
                "idempotency_key": str(idempotency_key),
                "batches": [{
                    "objects": [{
                        "type": "CATEGORY",
                        "id": cat_id,
                        "version": version_id,
                        "category_data": {
                            "name": request.json['name']
                        }
                    }]
                }]
            }
        )
        return jsonify(result.body)
    elif request.method == 'DELETE':
        result = app.config['client'].catalog.delete_catalog_object(
            object_id = cat_id
        )
        return jsonify(result.body)

@app.route('/v1/categories/<cat_id>/items', methods=['GET','POST'])
def categoryItems(cat_id):
    if request.method == 'GET':
        result = app.config['client'].catalog.search_catalog_objects(
            body = {
                "object_types": ["ITEM"],
                "query": {
                    "exact_query": {
                        "attribute_name": "category_id",
                        "attribute_value": cat_id
                    }
                }
            }
        )
        req = []
        try:
            for item in result.body['objects']:
                image_data = {}
                try:
                    item_result = app.config['client'].catalog.retrieve_catalog_object(
                        object_id = item['item_data']['image_ids'][0]
                    )
                    image_data = item_result.body['object']['image_data']
                except:
                    image_data = {
                        "url":None
                    }
                req.append({
                    'id':item['id'],
                    'name':item['item_data']['name'],
                    'price':item['item_data']['variations'][0]['item_variation_data']['price_money'],
                    'image_data':image_data
                })
        except:
            pass
        return jsonify(req)
    elif request.method == 'POST':
        idempotency_key = uuid.uuid4()
        result = app.config['client'].catalog.upsert_catalog_object(
            body = {
                "idempotency_key":str(idempotency_key),
                "object":{
                    "type":"ITEM",
                    "id":"#1",
                    "item_data":{
                        "name":request.json['name'],
                        "category_id":cat_id,
                        "variations":[
                            {
                                "type":"ITEM_VARIATION",
                                "id":"#2",
                                "item_variation_data":{
                                    "name":"Regular",
                                    "pricing_type":"FIXED_PRICING",
                                    "price_money":{
                                        "amount":request.json['price'],
                                        "currency":"USD"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        )
        return jsonify(result.body)

@app.route('/v1/items', methods=['GET','POST'])
def getItems():
    if request.method == 'GET':
        result = app.config['client'].catalog.list_catalog(
            types = "ITEM"
        )
        req = []
        for category in result.body['objects']:
            req.append({
                'version':category['version'],
                'id':category['id'],
                'name':category['item_data']['name']
            })
        return jsonify(req)

@app.route('/v1/items/<item_id>', methods=['GET', 'PUT', 'DELETE'])
def items(item_id):
    if request.method == 'GET':
        result = app.config['client'].catalog.retrieve_catalog_object(
            object_id = item_id
        )
        return jsonify(result.body['object'])
    elif request.method == 'PUT':
        idempotency_key = uuid.uuid4()
        result = app.config['client'].catalog.retrieve_catalog_object(
            object_id = item_id
        )
        version_id = result.body['object']['version']

        try:
            item_name = request.json['name']
        except:
            item_name = result.body['object']['item_data']['name']

        variations = result.body['object']['item_data']['variations']
        try:
            price_value = request.json['price']
        except:
            price_value = variations[0]['item_variation_data']['price_money']['amount']

        try:
            cat_id = request.json['category_id']
        except:
            cat_id = result.body['object']['item_data']['category_id']

        try:
            tax_id = [request.json['tax_id']]
        except:
            tax_id = [result.body['object']['item_data']['tax_ids'][0]]

        variations[0]['item_variation_data']['price_money']['amount'] = price_value
        result = app.config['client'].catalog.batch_upsert_catalog_objects(
            body = {
                "idempotency_key": str(idempotency_key),
                "batches": [{
                    "objects": [{
                        "type": "ITEM",
                        "id": item_id,
                        "version": version_id,
                        "item_data": {
                            "name": item_name,
                            "category_id":cat_id,
                            "variations":variations,
                            "tax_ids":tax_id
                        }
                    }]
                }]
            }
        )
        return jsonify(result.body)
    elif request.method == 'DELETE':
        result = app.config['client'].catalog.delete_catalog_object(
            object_id = item_id
        )
        return jsonify(result.body)

@app.route('/v1/orders', methods=['POST'])
def orders():
    idempotency_key = uuid.uuid4()
    print(request.json)
    result = app.config['client'].orders.create_order(
        body = {
            "order": {
                "location_id": "L75ER37CRBXNX",
                "line_items": request.json['line_items'],
                "taxes": request.json['taxes']
            },
            "idempotency_key": str(idempotency_key)
        }
    )
    order_id = result.body['order']['id']
    print(order_id)
    return jsonify(result.body)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)