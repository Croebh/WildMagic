import collections
import re

from disnake.ext.commands import BadArgument, ExpectedClosingQuoteError
from disnake.ext.commands.view import StringView

from cogsmisc.errors import InvalidArgument


def list_get(index, default, l):
    try:
        a = l[index]
    except IndexError:
        a = default
    return a


EPHEMERAL_ARG_RE = re.compile(r'([^\s]+)(\d+)')
QUOTE_PAIRS = {
    '"': '"',
    "'": "'",
    "‘": "’",
    "‚": "‛",
    "“": "”",
    "„": "‟",
    "⹂": "⹂",
    "「": "」",
    "『": "』",
    "〝": "〞",
    "﹁": "﹂",
    "﹃": "﹄",
    "＂": "＂",
    "｢": "｣",
    "«": "»",
    "‹": "›",
    "《": "》",
    "〈": "〉",
}
ALL_QUOTES = set(QUOTE_PAIRS.keys()) | set(QUOTE_PAIRS.values())


def argsplit(args: str):
    view = CustomStringView(args.strip())
    args = []
    while not view.eof:
        view.skip_ws()
        args.append(view.get_quoted_word())  # _quoted_word(view))
    return args


def argparse(args, splitter=argsplit):
    """
    Parses arguments.
    :param args: A list of arguments to parse.
    :type args: str or Iterable
    :return: The parsed arguments.
    :rtype: :class:`~utils.argparser.ParsedArguments`
    """
    if isinstance(args, str):
        args = splitter(args)

    parsed = collections.defaultdict(lambda: [])
    index = 0
    for a in args:
        if a.startswith('-'):
            parsed[a.lstrip('-')].append(list_get(index + 1, True, args))
        else:
            parsed[a].append(True)
        index += 1
    return ParsedArguments(parsed)


def argquote(arg: str):
    if ' ' in arg:
        arg = arg.replace("\"", "\\\"")  # re.sub(r'(?<!\\)"', r'\"', arg)
        arg = f'"{arg}"'
    return arg


class ParsedArguments:
    def __init__(self, parsed):
        self._parsed = parsed

        # contextual support
        self._original_parsed = collections.defaultdict(lambda: [])
        self._setup_originals()
        self._contexts = collections.defaultdict(lambda: ParsedArguments.empty_args())

    @classmethod
    def from_dict(cls, d):
        inst = cls(collections.defaultdict(lambda: []))
        for key, value in d.items():
            inst[key] = value
        return inst

    @classmethod
    def empty_args(cls):
        return cls(collections.defaultdict(lambda: []))

    # basic argument getting
    def get(self, arg, default=None, type_=str):
        """
        Gets a list of all values of an argument.
        :param str arg: The name of the arg to get.
        :param default: The default value to return if the arg is not found. Not cast to type.
        :param type_: The type that each value in the list should be returned as.
        :return: The relevant argument list.
        :rtype: list
        """
        if default is None:
            default = []
        parsed = self._get_values(arg)
        if not parsed:
            return default
        try:
            return [type_(v) for v in parsed]
        except (ValueError, TypeError):
            raise InvalidArgument(f"One or more arguments cannot be cast to {type_.__name__} (in `{arg}`)")

    def last(self, arg, default=None, type_: type = str):
        """
        Gets the last value of an arg.
        :param str arg: The name of the arg to get.
        :param default: The default value to return if the arg is not found. Not cast to type.
        :param type_: The type that the arg should be returned as.
        :raises: InvalidArgument if the arg cannot be cast to the type
        :return: The relevant argument.
        """
        last_arg = self._get_last(arg)
        if last_arg is None:
            return default
        try:
            return type_(last_arg)
        except (ValueError, TypeError):
            raise InvalidArgument(f"{last_arg} cannot be cast to {type_.__name__} (in `{arg}`)")

    def join(self, arg, connector: str, default=None):
        """
        Returns a str formed from all of one arg, joined by a connector.
        :param arg: The arg to join.
        :param connector: What to join the arg by.
        :param default: What to return if the arg does not exist.
        :return: The joined str, or default.
        """
        return connector.join(self.get(arg)) or default

    def ignore(self, arg):
        """
        Removes any instances of an argument from the result in all contexts (ephemeral included).
        :param arg: The argument to ignore.
        """
        del self[arg]
        for context in self._contexts.values():
            del context[arg]

    def update(self, new):
        """
        Updates the arguments in this argument list from a dict.
        :param new: The new values for each argument.
        :type new: dict[str, str] or dict[str, list[str]]
        """
        for k, v in new.items():
            self[k] = v

    def update_nx(self, new):
        """
        Like ``.update()``, but only fills in arguments that were not already parsed. Ignores the argument if the
        value is None.
        :param new: The new values for each argument.
        :type new: dict[str, str] or dict[str, list[str]] or dict[str, None]
        """
        for k, v in new.items():
            if k not in self and v is not None:
                self[k] = v

    # get helpers
    def _get_values(self, arg):
        """Returns a list of arguments."""
        return self._parsed[arg]

    def _get_last(self, arg):
        """Returns the last argument."""
        if arg in self._parsed and self._parsed[arg]:
            return self._parsed[arg][-1]
        return None

    # context helpers
    def _setup_originals(self):
        for arg, values in self._parsed.items():
            self._original_parsed[arg] = values.copy()

    def set_context(self, context):
        """
        Sets the current argument parsing context.
        :param context: Any hashable context.
        """
        if context is None:
            self._parsed = self._original_parsed
        else:
            # build a new parsed and ephemeral list
            new_parsed = collections.defaultdict(lambda: [])
            for arg, values in self._original_parsed.items():
                new_parsed[arg].extend(values)

            for arg, values in self._contexts[context]._parsed.items():
                new_parsed[arg].extend(values)

            self._parsed = new_parsed

    def add_context(self, context, args):
        """
        Adds contextual parsed arguments (arguments that only apply in a given context)
        :param context: The context to add arguments to.
        :param args: The arguments to add.
        :type args: :class:`~utils.argparser.ParsedArguments`
        """
        self._contexts[context] = args

    # builtins
    def __contains__(self, item):
        return item in self._parsed and self._parsed[item]

    def __len__(self):
        return len(self._parsed)

    def __setitem__(self, key, value):
        """
        :type key: str
        :type value: str or bool or list[str or bool]
        """
        if not isinstance(value, (collections.UserList, list)):
            value = [value]
        self._parsed[key] = value
        self._original_parsed[key] = value.copy()

    def __delitem__(self, arg):
        """
        Removes any instances of an argument from the result in the current context (ephemeral included).
        :param arg: The argument to ignore.
        """
        for container in (self._parsed, self._original_parsed):
            if arg in container:
                del container[arg]

    def __iter__(self):
        return iter(self._parsed.keys())

    def __repr__(self):
        return f"<ParsedArguments parsed={self._parsed.items()}>"


class CustomStringView(StringView):
    def get_quoted_word(self):
        current = self.current
        if current is None:
            return None

        close_quote = QUOTE_PAIRS.get(current)
        is_quoted = bool(close_quote)
        if is_quoted:
            result = []
            _escaped_quotes = (current, close_quote)
        else:
            result = [current]
            _escaped_quotes = ALL_QUOTES

        while not self.eof:
            current = self.get()
            if not current:
                if is_quoted:
                    # unexpected EOF
                    raise ExpectedClosingQuoteError(close_quote)
                return ''.join(result)

            # currently we accept strings in the format of "hello world"
            # to embed a quote inside the string you must escape it: "a \"world\""
            if current == '\\':
                next_char = self.get()
                if next_char in _escaped_quotes:
                    # escaped quote
                    result.append(next_char)
                else:
                    # different escape character, ignore it
                    self.undo()
                    result.append(current)
                continue

            # opening quote
            if not is_quoted and current in ALL_QUOTES and current != "'":  # special case: apostrophes in mid-string
                close_quote = QUOTE_PAIRS.get(current)
                is_quoted = True
                _escaped_quotes = (current, close_quote)
                continue

            # closing quote
            if is_quoted and current == close_quote:
                next_char = self.get()
                valid_eof = not next_char or next_char.isspace()
                if not valid_eof:  # there's still more in this argument
                    self.undo()
                    close_quote = None
                    is_quoted = False
                    _escaped_quotes = ALL_QUOTES
                    continue

                # we're quoted so it's okay
                return ''.join(result)

            if current.isspace() and not is_quoted:
                # end of word found
                return ''.join(result)

            result.append(current)


if __name__ == '__main__':
    while True:
        try:
            print(argsplit(input('>>> ')))
        except BadArgument as e:
            print(e)

