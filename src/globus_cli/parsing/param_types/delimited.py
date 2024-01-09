from __future__ import annotations

import typing as t

import click


class CommaDelimitedList(click.ParamType):
    def __init__(
        self,
        *,
        convert_values: t.Callable[[str], str] | None = None,
        choices: t.Iterable[str] | None = None,
    ) -> None:
        super().__init__()
        self.convert_values = convert_values
        self.choices = list(choices) if choices is not None else None

    def get_metavar(self, param: click.Parameter) -> str:
        if self.choices is not None:
            return "{" + ",".join(self.choices) + "}"
        return "TEXT,TEXT,..."

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> list[str]:
        value = super().convert(value, param, ctx)

        # if `--foo` is a comma delimited list and someone passes
        # `--foo ""`, take that as `foo=[]` rather than foo=[""]
        #
        # the alternative is fine, but we have to choose one and this is
        # probably "closer to what the caller meant"
        #
        # it means that if you take
        # `--foo={",".join(original)}`, you will get a value equal to
        # `original` back if `original=[]` (but not if `original=[""]`)
        resolved = value.split(",") if value else []

        if self.convert_values is not None:
            resolved = [self.convert_values(x) for x in resolved]

        if self.choices is not None:
            bad_values = [x for x in resolved if x not in self.choices]
            if bad_values:
                self.fail(
                    f"the values {bad_values} were not valid choices",
                    param=param,
                    ctx=ctx,
                )

        return resolved


class ColonDelimitedChoiceTuple(click.Choice):
    def __init__(
        self,
        *,
        choices: t.Sequence[str],
        case_sensitive: bool = True,
    ) -> None:
        super().__init__(choices, case_sensitive=case_sensitive)

        self.unpacked_choices = self._unpack_choices()

    def _unpack_choices(self) -> list[tuple[str, ...]]:
        split_choices = [tuple(choice.split(":")) for choice in self.choices]
        if len(split_choices) == 0:
            raise NotImplementedError("No choices")
        choice_len = len(split_choices[0])
        if any(len(choice) != choice_len for choice in split_choices):
            raise NotImplementedError("Not all choices have the same length")
        return split_choices

    def get_type_annotation(self, param: click.Parameter) -> type:
        # convert tuples of choices to a tuple of literals of choices
        #
        # the transformation is tricky, but it effectively does this:
        #     [(1, 3), (2, 4)] -> tuple[Literal[1, 2], Literal[3, 4]]

        # unzip/transpose using zip(*x)
        unzipped_choices = zip(*self.unpacked_choices)

        # each tuple of choices becomes a Literal
        literals = [t.Literal[choices] for choices in unzipped_choices]

        # runtime calls to __class_getitem__ require a single tuple argument
        # so we explicitly `tuple(...)` to get the right data shape
        # type-ignore because mypy complains about multiple errors due to
        # its misunderstanding of a runtime-only __class_getitem__ usage
        return tuple[tuple(literals)]  # type: ignore

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> tuple[str, ...]:
        return tuple(super().convert(value, param, ctx).split(":"))
