import utils
import falcon
import json

from model import model
from templates_engine import render

model.open_model()


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


class SquadsInfoByTag:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, tag: str, details_type: str) -> None:
        """
        Params to request:
        resolve_tags: bool
        pretty_keys: bool

        :param details_type: short or extended, extended includes tags
        :param req:
        :param resp:
        :param tag:
        :return:
        """

        resp.content_type = falcon.MEDIA_JSON
        details_type = details_type.lower()

        if details_type == 'short':
            model_method = model.list_squads_by_tag

        elif details_type == 'extended':
            model_method = model.list_squads_by_tag_with_tags

        else:
            raise falcon.HTTPBadRequest(description=f'details_type must be one of short, extended')

        resolve_tags = req.params.get('resolve_tags', '').lower() == 'true'
        pretty_keys = req.params.get('pretty_keys', 'true').lower() == 'true'

        model_answer = model_method(tag, pretty_keys=pretty_keys)

        if resolve_tags and details_type == 'extended':
            if pretty_keys:
                user_tags_key = 'User tags'

            else:
                user_tags_key = 'user_tags'

            for squad in model_answer:
                squad[user_tags_key] = utils.humanify_resolved_user_tags(utils.resolve_user_tags(squad[user_tags_key]))

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
application.add_route('/squads/now/by-tag/short/{tag}', SquadsInfoByTagShortHtml())

application.add_route('/api/squads/now/by-tag/{details_type}/{tag}', SquadsInfoByTag())
application.add_route('/squads/now/by-tag/extended/{tag}', SquadsInfoByTagExtendedHtml())

if __name__ == '__main__':
    model.open_model()
    import waitress
    import os
    application.add_static_route('/js', os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), 'js'))
    waitress.serve(application, host='127.0.0.1', port=9486)
