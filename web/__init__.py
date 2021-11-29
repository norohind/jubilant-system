import os
import falcon
import json

from model import model
from web import dynamic_js


class SquadsInfoByTag:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, tag: str) -> None:
        resp.content_type = falcon.MEDIA_JSON
        resp.text = json.dumps(model.list_squads_by_tag(tag))


class SquadsInfoByTagHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, tag: str) -> None:
        resp.content_type = falcon.MEDIA_HTML
        model_answer = model.list_squads_by_tag(tag)

        # for squad in model_answer:
        #     squad['User tags'] = utils.humanify_resolved_user_tags(utils.resolve_user_tags(squad['User tags']))

        resp.text = dynamic_js.activity_table_html_template.replace('{items}', json.dumps(model_answer))


application = falcon.App()
application.add_route('/api/squads/now/by-tag/{tag}', SquadsInfoByTag())
application.add_route('/squads/now/by-tag/{tag}', SquadsInfoByTagHtml())

if __name__ == '__main__':
    model.open_model()
    import waitress
    import os
    application.add_static_route('/js', os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), 'js'))
    waitress.serve(application, host='127.0.0.1', port=9486)
