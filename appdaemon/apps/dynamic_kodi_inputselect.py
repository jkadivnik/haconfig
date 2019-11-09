import appdaemon.plugins.hass.hassapi as hass

EVENT_KODI_CALL_METHOD_RESULT = 'kodi_call_method_result'

class DynamicKodiInputSelect(hass.Hass):
    """AppDaemon app to dynamically populate an `input_select`."""
    _ids_options = None

    def initialize(self):
        self._movie_inputselect_entity = self.args.get('movie_inputselect', str)
        self._series_inputselect_entity = self.args.get('series_inputselect', str)
        self._kodi_entity = self.args.get('kodi_entity', str)
        self._movies_max_entries = int(self.args.get('movies_max_entries', 10))
        self._series_max_entries = int(self.args.get('movies_max_entries', 10))

        self.listen_event(self._receive_kodi_result,EVENT_KODI_CALL_METHOD_RESULT)
        self._ids_options = {"Kodi Results": None}

    def _receive_kodi_result(self, event_id, payload_event, *args):
        result = payload_event['result']
        method = payload_event['input']['method']

        assert event_id == EVENT_KODI_CALL_METHOD_RESULT
        if method == 'VideoLibrary.GetRecentlyAddedMovies':
            values = result['movies'][:self._movies_max_entries]
            data = [('{} ({})'.format(r['label'], r['year']), ('MOVIE', r['file'])) for r in values]
            self._ids_options.update(dict(zip(*zip(*data))))
            labels = list(list(zip(*data))[0])
            self.call_service('input_select/set_options', entity_id=self._movie_inputselect_entity, options=["Select a movie to watch"] + labels)
            self.set_state(self._movie_inputselect_entity, attributes={"friendly_name": 'Recent Movies', "icon": 'mdi:movie'})
            self.listen_state(self._change_selected_option, self._movie_inputselect_entity)
        elif method == 'VideoLibrary.GetRecentlyAddedEpisodes':
            values = list(filter(lambda r: not r['lastplayed'], result['episodes']))[:self._series_max_entries]
            data = [('{} - {}'.format(r['showtitle'], r['label']), ('TVSHOW', r['file'])) for r in values]
            self._ids_options.update(dict(zip(*zip(*data))))
            labels = list(list(zip(*data))[0])
            self.call_service('input_select/set_options', entity_id=self._series_inputselect_entity, options=["Select an episode to watch"] + labels)
            self.set_state(self._series_inputselect_entity, attributes={"friendly_name": 'Recent TvShows', "icon": 'mdi:filmstrip'})
            self.listen_state(self._change_selected_option, self._series_inputselect_entity)

    def _change_selected_option(self, entity, attribute, old, new, kwargs):
        selected = self._ids_options[new]
        if selected:
            mediatype, file = selected
            self.call_service('media_player/play_media', entity_id=self._kodi_entity, media_content_type=mediatype, media_content_id=file)