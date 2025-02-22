import sickchill
from sickchill import logger, settings
from sickchill.oldbeard.trakt_api import TraktAPI, traktAuthException, traktException, traktServerBusy


class Notifier(object):
    """
    A "notifier" for trakt.tv which keeps track of what has and hasn't been added to your library.
    """

    def notify_snatch(self, ep_name):
        pass

    def notify_download(self, ep_name):
        pass

    def notify_subtitle_download(self, ep_name, lang):
        pass

    def notify_update(self, new_version):
        pass

    def notify_login(self, ipaddress=""):
        pass

    @staticmethod
    def update_library(episode_object):
        """
        Sends a request to trakt indicating that the given episode is part of our library.

        episode_object: The TVEpisode object to add to trakt
        """

        trakt_api = TraktAPI(settings.SSL_VERIFY, settings.TRAKT_TIMEOUT)

        if settings.USE_TRAKT:
            try:
                # URL parameters
                data = {
                    "shows": [
                        {
                            "title": episode_object.show.name,
                            "year": episode_object.show.startyear,
                            "ids": {episode_object.idxr.slug: episode_object.show.indexerid},
                        }
                    ]
                }

                if settings.TRAKT_SYNC_WATCHLIST and settings.TRAKT_REMOVE_SERIESLIST:
                    trakt_api.traktRequest("sync/watchlist/remove", data, method="POST")

                # Add Season and Episode + Related Episodes
                data["shows"][0]["seasons"] = [{"number": episode_object.season, "episodes": []}]

                for relEp_Obj in [episode_object] + episode_object.related_episodes:
                    data["shows"][0]["seasons"][0]["episodes"].append({"number": relEp_Obj.episode})

                if settings.TRAKT_SYNC_WATCHLIST and settings.TRAKT_REMOVE_WATCHLIST:
                    trakt_api.traktRequest("sync/watchlist/remove", data, method="POST")

                # update library
                trakt_api.traktRequest("sync/collection", data, method="POST")

            except (traktException, traktAuthException, traktServerBusy) as error:
                logger.warning(f"Could not connect to Trakt service: {error}")

    @staticmethod
    def update_watchlist(show_obj=None, data_show=None, data_episode=None, update="add"):
        """
        Sends a request to trakt indicating that the given episode is part of our library.

        show_obj: The TVShow object to add to trakt
        s: season number
        e: episode number
        data_show: structured object of shows trakt type
        data_episode: structured object of episodes trakt type
        update: type of action add or remove
        """

        trakt_api = TraktAPI(settings.SSL_VERIFY, settings.TRAKT_TIMEOUT)

        if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
            data = {}
            try:
                # URL parameters
                if show_obj:
                    data = {
                        "shows": [
                            {
                                "title": show_obj.name,
                                "year": show_obj.startyear,
                                "ids": {show_obj.idxr.slug: show_obj.indexerid},
                            }
                        ]
                    }
                elif data_show:
                    data.update(data_show)
                else:
                    logger.warning("there's a coding problem contact developer. It's needed to be provided at lest one of the two: data_show or show_obj")
                    return False

                if data_episode:
                    data["shows"][0].update(data_episode)

                trakt_url = "sync/watchlist"
                if update == "remove":
                    trakt_url += "/remove"

                trakt_api.traktRequest(trakt_url, data, method="POST")

            except (traktException, traktAuthException, traktServerBusy) as error:
                logger.warning(f"Could not connect to Trakt service: {error}")
                return False

        return True

    @staticmethod
    def trakt_show_data_generate(data):
        showList = []
        # TODO: is indexer and indexerid swapped here or in traktChecker:591? !Important
        for indexer, indexerid, title, year in data:
            show = {"title": title, "year": year, "ids": {sickchill.indexer.slug(indexer): indexerid}}
            showList.append(show)

        post_data = {"shows": showList}

        return post_data

    @staticmethod
    def trakt_episode_data_generate(data):
        # Find how many unique season we have
        uniqueSeasons = []
        for season, episode in data:
            if season not in uniqueSeasons:
                uniqueSeasons.append(season)

        # build the query
        seasonsList = []
        for searchedSeason in uniqueSeasons:
            episodesList = []
            for season, episode in data:
                if season == searchedSeason:
                    episodesList.append({"number": episode})
            seasonsList.append({"number": searchedSeason, "episodes": episodesList})

        post_data = {"seasons": seasonsList}

        return post_data

    @staticmethod
    def test_notify(username, blacklist_name=None):
        """
        Sends a test notification to trakt with the given authentication info and returns a boolean
        representing success.

        api: The api string to use
        username: The username to use
        blacklist_name: slug of trakt list used to hide not interested show

        Returns: True if the request succeeded, False otherwise
        """
        try:
            trakt_api = TraktAPI(settings.SSL_VERIFY, settings.TRAKT_TIMEOUT)
            trakt_api.validateAccount()
            if blacklist_name:
                trakt_lists = trakt_api.traktRequest("users/" + username + "/lists")
                found = False
                for trakt_list in trakt_lists:
                    if trakt_list["ids"]["slug"] == blacklist_name:
                        return "Test notice sent successfully to Trakt"
                if not found:
                    return "Trakt blacklist doesn't exists"
            else:
                return "Test notice sent successfully to Trakt"
        except (traktException, traktAuthException, traktServerBusy) as error:
            logger.warning(f"Could not connect to Trakt service: {error}")
            return f"Test notice failed to Trakt: {error}"
