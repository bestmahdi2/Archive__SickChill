from tornado.web import addslash

from sickchill import settings
from sickchill.oldbeard import config
from sickchill.views.common import PageTemplate
from sickchill.views.home import Home
from sickchill.views.routes import Route


@Route("/home/postprocess(/?.*)", name="home:postprocess")
class PostProcess(Home):
    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="home_postprocess.mako")
        return t.render(title=_("Post Processing"), header=_("Post Processing"), topmenu="home", controller="home", action="postProcess")

    def processEpisode(
        self,
        proc_dir=None,
        nzbName=None,
        quiet=None,
        process_method=None,
        force=None,
        is_priority=None,
        delete_on="0",
        failed="0",
        proc_type="manual",
        force_next=False,
        *args_,
        **kwargs,
    ):
        mode = kwargs.get("type", proc_type)
        process_path = self.get_argument("dir", default=self.get_argument("proc_dir", default=""))
        if not process_path:
            return self.redirect("/home/postprocess/")

        release_name = self.get_argument("nzbName", default=None)

        result = settings.postProcessorTaskScheduler.action.add_item(
            process_path,
            release_name,
            method=process_method,
            force=force,
            is_priority=is_priority,
            delete=delete_on,
            failed=failed,
            mode=mode,
            force_next=force_next,
        )

        if config.checkbox_to_value(quiet):
            return result

        if result:
            result = result.replace("\n", "<br>\n")

        return self._genericMessage("Postprocessing results", result)
