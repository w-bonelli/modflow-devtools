from io import BytesIO, StringIO
from typing import Optional

from modflow_devtools.imports import import_optional_dependency

np = import_optional_dependency("numpy")
pytest = import_optional_dependency("pytest")
syrupy = import_optional_dependency("syrupy")

# ruff: noqa: E402
from syrupy.extensions.single_file import (
    SingleFileSnapshotExtension,
    WriteMode,
)
from syrupy.types import (
    PropertyFilter,
    PropertyMatcher,
    SerializableData,
    SerializedData,
)

# extension classes


class BinaryArrayExtension(SingleFileSnapshotExtension):
    """
    Binary snapshot of a NumPy array. Can be read back into NumPy with
    .load(), preserving dtype and shape. This is the recommended array
    snapshot approach if human-readability is not a necessity, as disk
    space is minimized.
    """

    _write_mode = WriteMode.BINARY
    _file_extension = "npy"

    def serialize(
        self,
        data,
        *,
        exclude=None,
        include=None,
        matcher=None,
    ):
        buffer = BytesIO()
        np.save(buffer, data)
        return buffer.getvalue()


class TextArrayExtension(SingleFileSnapshotExtension):
    """
    Text snapshot of a NumPy array. Flattens the array before writing.
    Can be read back into NumPy with .loadtxt() assuming you know the
    shape of the expected data and subsequently reshape it if needed.
    """

    _write_mode = WriteMode.TEXT
    _file_extension = "txt"

    def serialize(
        self,
        data: "SerializableData",
        *,
        exclude: Optional["PropertyFilter"] = None,
        include: Optional["PropertyFilter"] = None,
        matcher: Optional["PropertyMatcher"] = None,
    ) -> "SerializedData":
        buffer = StringIO()
        np.savetxt(buffer, data.ravel())
        return buffer.getvalue()


class ReadableArrayExtension(SingleFileSnapshotExtension):
    """
    Human-readable snapshot of a NumPy array. Preserves array shape
    at the expense of possible loss of precision (default 8 places)
    and more difficulty loading into NumPy than TextArrayExtension.
    """

    _write_mode = WriteMode.TEXT
    _file_extension = "txt"

    def serialize(
        self,
        data: "SerializableData",
        *,
        exclude: Optional["PropertyFilter"] = None,
        include: Optional["PropertyFilter"] = None,
        matcher: Optional["PropertyMatcher"] = None,
    ) -> "SerializedData":
        return np.array2string(data, threshold=np.inf)


# fixtures


@pytest.fixture
def array_snapshot(snapshot):
    return snapshot.use_extension(BinaryArrayExtension)


@pytest.fixture
def text_array_snapshot(snapshot):
    return snapshot.use_extension(TextArrayExtension)


@pytest.fixture
def readable_array_snapshot(snapshot):
    return snapshot.use_extension(ReadableArrayExtension)
