"""Simple OOP example modeling a pipeline run."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class PipelineRun:
    pipeline_name: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    rows_processed: int = 0
    errors: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def is_successful(self) -> bool:
        return not self.errors


def main() -> None:
    run = PipelineRun(pipeline_name="orders_etl")
    run.rows_processed = 1500
    run.add_error("schema drift in column country")
    print(run, run.is_successful())


if __name__ == "__main__":
    main()
