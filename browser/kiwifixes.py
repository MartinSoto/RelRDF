import re

import gtk

import kiwi.ui.delegates
import kiwi.ui.views

class UiManagerSignalBroker(object):
    def _do_connections(self, view, methods):
        self._autoconnectUiManager(view, methods)
        super(UiManagerSignalBroker, self)._do_connections(view, methods)

    def _autoconnectUiManager(self, view, methods):
        for group in view.uiManager.get_action_groups():
            for action in group.list_actions():
                pattern = re.compile(r'^(on|after)_%s__(\w+)' %
                                     action.get_name())
                for methodName in tuple(methods.keys()):
                    match = pattern.match(methodName)
                    if match is None:
                        continue

                    after, signal = match.groups()
                    method = getattr(view, methodName)
                    if after == 'after':
                        action.connect_after(signal, method)
                    else:
                        action.connect(signal, method)

                    del methods[methodName]


class SignalBroker(UiManagerSignalBroker,
                   kiwi.ui.views.SignalBroker):
    pass

class GladeSignalBroker(UiManagerSignalBroker,
                        kiwi.ui.views.GladeSignalBroker):
    pass


class UiManagerSlaveView(object):
    """A view extension that adds a GTK UIManager and configures and
    connects it automatically based on object/class attributes."""

    _actionRegex = re.compile(r'^(\w+)__actions$')
    _toggleActionRegex = re.compile(r'^(\w+)__toggleActions$')

    def __init__(self, *args, **kwargs):
        self.uiManager = gtk.UIManager()

        # Create actions and action groups.
        # FIXME: Do not rely on dir for doing this.
        for name in dir(self):
            match = self._actionRegex.match(name)
            if match is not None:
                groupName, = match.groups()
                actionGroup = self._getActionGroup(groupName)
                actionGroup.add_actions(getattr(self, name))

            match = self._toggleActionRegex.match(name)
            if match is not None:
                groupName, = match.groups()
                actionGroup = self._getActionGroup(groupName)
                actionGroup.add_toggle_actions(getattr(self, name))

        # Add all actions as attributes.
        for group in self.uiManager.get_action_groups():
            for action in group.list_actions():
                setattr(self, action.get_name(), action)

        super(UiManagerSlaveView, self).__init__(*args, **kwargs)

        # Add UI definitions to the UIManager.
        if hasattr(self, 'uiDefinition'):
            self.uiManager.add_ui_from_string(self.uiDefinition)

    def _attach_callbacks(self, controller):
        if self._glade_adaptor is None:
            brokerclass = SignalBroker
        else:
            brokerclass = GladeSignalBroker

        self._broker = brokerclass(self, controller)


class UiManagerDelegate(UiManagerSlaveView, kiwi.ui.delegates.Delegate):
    pass

class UiManagerSlaveDelegate(UiManagerSlaveView,
                             kiwi.ui.delegates.SlaveDelegate):
    pass

