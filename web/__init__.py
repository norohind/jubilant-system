import utils
import falcon
import json

from model import model
from templates_engine import render

model.open_model()


class SquadsInfoByTagShort:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, tag: str) -> None:
        resp.content_type = falcon.MEDIA_JSON
        resp.text = json.dumps(model.list_squads_by_tag(tag))


class SquadsInfoByTagShortHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, tag: str) -> None:
        resp.content_type = falcon.MEDIA_HTML
        resp.text = render(
            'table_template.html',
            {
                'target_column_name': 'None',
                'target_new_url': ''
            }
        )


class SquadsInfoByTagExtended:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, tag: str) -> None:
        resp.content_type = falcon.MEDIA_JSON
        model_answer = model.list_squads_by_tag_with_tags(tag)

        for squad in model_answer:
            squad['user_tags'] = utils.humanify_resolved_user_tags(utils.resolve_user_tags(squad['user_tags']))

        resp.text = json.dumps(model_answer)


class SquadsInfoByTagExtendedHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, tag: str) -> None:
        resp.content_type = falcon.MEDIA_HTML
        resp.text = render(
            'table_template.html',
            {
                'target_column_name': 'None',
                'target_new_url': ''
            }
        )


application = falcon.App()
application.add_route('/api/squads/now/by-tag/short/{tag}', SquadsInfoByTagShort())
application.add_route('/squads/now/by-tag/short/{tag}', SquadsInfoByTagShortHtml())

application.add_route('/api/squads/now/by-tag/extended/{tag}', SquadsInfoByTagExtended())
application.add_route('/squads/now/by-tag/extended/{tag}', SquadsInfoByTagExtendedHtml())

if __name__ == '__main__':
    model.open_model()
    import waitress
    import os
    application.add_static_route('/js', os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), 'js'))
    waitress.serve(application, host='127.0.0.1', port=9486)
