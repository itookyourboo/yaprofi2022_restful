from dataclasses import dataclass, field, asdict


@dataclass
class Prize:
    id: int
    description: str


@dataclass
class Participant:
    id: int
    name: str


@dataclass
class Promo:
    id: int
    name: str
    description: str | None
    prizes: list[Prize] = field(default_factory=list)
    participants: list[Participant] = field(default_factory=list)

    def short_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

    def full_dict(self, prize_map, participant_map):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "prizes": list(map(prize_map, self.prizes)),
            "participants": list(map(participant_map, self.participants))
        }
