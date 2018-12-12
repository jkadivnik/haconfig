import hassapi as hass
from homeassistant.components.media_player.kodi import (EVENT_KODI_CALL_METHOD_RESULT)

ENTITY = 'input_select.kodi_results'
MEDIA_PLAYER = 'media_player.kodi'
DEFAULT_ACTION = "Nothing to do"
MAX_RESULTS = 20

class DynamicKodiInputSelect(appapi.AppDaemon):
    """AppDaemon app to dynamically populate an `input_select`."""
    _ids_options = None

    def initialize(self):
        self._movie_inputselect_entity = self.args.get('movie_inputselect', str)
        self._series_inputselect_entity = self.args.get('series_inputselect', str)
        self._kodi_entity = self.args.get('kodi_entity', str)
        self._max_entries = int(self.args.get('max_entries', 10))

        self.listen_event(self._receive_kodi_result,EVENT_KODI_CALL_METHOD_RESULT)
        # Input select:
        self._ids_options = {"Kodi Results": None}

    def _receive_kodi_result(self, event_id, payload_event, *args):
        result = payload_event['result']
        method = payload_event['input']['method']

        assert event_id == EVENT_KODI_CALL_METHOD_RESULT
        if method == 'VideoLibrary.GetRecentlyAddedMovies':
            values = result['movies'][:self._max_entries]
            data = [('{} ({})'.format(r['label'], r['year']), ('MOVIE', r['file'])) for r in values]
            self._ids_options.update(dict(zip(*zip(*data))))
            labels = list(list(zip(*data))[0])
            self.call_service('input_select/set_options', entity_id=self._movie_inputselect_entity, options=["Movies not filled"] + labels)
            self.set_state(self._movie_inputselect_entity, attributes={"friendly_name": 'Recent Movies', "icon": 'mdi:movie'})
        elif method == 'VideoLibrary.GetRecentlyAddedEpisodes':
            values = list(filter(lambda r: not r['lastplayed'], result['episodes']))[:self._max_entries]
            data = [('{} - {}'.format(r['showtitle'], r['label']), ('TVSHOW', r['file'])) for r in values]
            self._ids_options.update(dict(zip(*zip(*data))))
            labels = list(list(zip(*data))[0])
            self.call_service('input_select/set_options', entity_id=self._series_inputselect_entity, options=["Series not filled"] + labels)
            self.set_state(self._series_inputselect_entity, attributes={"friendly_name": 'Recent TvShows', "icon": 'mdi:play-circle'})

    def _change_selected_option(self, entity, attribute, old, new, kwargs):
        selected = self._ids_options[new]
        if selected:
            mediatype, file = selected
            self.call_service('media_player/play_media', entity_id=self._kodi_entity, media_content_type=mediatype, media_content_id=file)