from dataclasses import dataclass, field

@dataclass
class GUI():

    title: str
    geometry: str
    queryfiles: set = field(default_factory=set) 
    queries: list = field(default_factory=list)

    def add_device(self, queryfile: str, queries: list) -> None:
        self.queryfiles.add(queryfile)
        self.queries.extend(queries)

