"""
base.py
=======
Abstract root classes of the whole object model.

Hierarchy
---------
Entity (ABC)
 └── CompositeEntity[T] (ABC, Generic)   – an Entity that owns child Entities
"""
from __future__ import annotations

from abc import ABC
from typing import Any, Callable, Dict, Generic, Iterator, List, Optional, Type, TypeVar


class Entity(ABC):
    """Root class for every identifiable object (rig, plane, sector, point, sensor, ...)."""

    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id: str = id or name
        self.name: str = name
        self.description: str = description
        self.metadata: Dict[str, Any] = dict(metadata or {})
        self.parent: Optional["CompositeEntity"] = None

    # ------------------------------------------------------------------
    @property
    def path(self) -> str:
        """Full hierarchical path, e.g. 'RigA/PlaneE1/Sector1/PT01'."""
        return f"{self.parent.path}/{self.id}" if self.parent else self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": type(self).__name__,
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "path": self.path,
            **self.metadata,
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id!r})"


T = TypeVar("T", bound=Entity)


class CompositeEntity(Entity, Generic[T]):
    """Entity that owns an ordered collection of child entities of type ``child_type``."""

    child_type: Type[Entity] = Entity

    def __init__(self, name: str, **kwargs: Any) -> None:
        super().__init__(name, **kwargs)
        self._children: Dict[str, T] = {}

    # ---- child management --------------------------------------------
    def add(self, child: T) -> T:
        if not isinstance(child, self.child_type):
            raise TypeError(
                f"{type(self).__name__} accepts only {self.child_type.__name__}, "
                f"got {type(child).__name__}"
            )
        if child.id in self._children:
            raise KeyError(f"Duplicate id '{child.id}' in {self.path}")
        child.parent = self
        self._children[child.id] = child
        return child

    def remove(self, child_id: str) -> T:
        child = self._children.pop(child_id)
        child.parent = None
        return child

    def get(self, child_id: str) -> T:
        try:
            return self._children[child_id]
        except KeyError:
            raise KeyError(f"'{child_id}' not found in {self.path}") from None

    @property
    def children(self) -> List[T]:
        return list(self._children.values())

    def find(self, predicate: Callable[[T], bool]) -> List[T]:
        return [c for c in self._children.values() if predicate(c)]

    def walk(self) -> Iterator[Entity]:
        """Depth-first iteration over all descendants."""
        for child in self._children.values():
            yield child
            if isinstance(child, CompositeEntity):
                yield from child.walk()

    # ---- dunder helpers ----------------------------------------------
    def __iter__(self) -> Iterator[T]:
        return iter(self._children.values())

    def __len__(self) -> int:
        return len(self._children)

    def __contains__(self, child_id: object) -> bool:
        return child_id in self._children

    def __getitem__(self, child_id: str) -> T:
        return self.get(child_id)
