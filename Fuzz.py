from typing import List,Union
import subprocess
import random
class Runner:
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESLOVED = "RESELOVED"

    def __init__(self) -> None:
        pass

    def run(self, inp: str):
        return (inp, Runner.UNRESLOVED)


class ProgramRunner(Runner):
    def __init__(self, program: Union[str, List[str]]):
        self.program = program

    def run_process(self, inp: str = ""):
        return subprocess.run(self.program,
                              input=inp,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True,
                              shell=True
                              )

    def run(self, inp: str = ""):
        result = self.run_process(inp)

        if result.returncode == 0:
            outcome = self.PASS
        elif result.returncode < 0:
            outcome = self.FAIL
        else:
            outcome = self.UNRESLOVED
        return (result, outcome)


class BinaryProgramRunner(ProgramRunner):
    def run_process(self, inp: str = "") -> subprocess.CompletedProcess:
        """Run the program with `inp` as input.  
           Return result of `subprocess.run()`."""
        return subprocess.run(self.program,
                              input=inp.encode(),
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)


class Fuzzer:
    def __init__(self) -> None:
        pass

    def fuzz(self) -> str:
        return

    def run(self, runner: Runner = Runner()):
        return runner.run(self.fuzz())

    def runs(self, runner: Runner = Runner(), trials: int = 10):
        return [self.run(runner) for i in range(trials)]


class RandomFuzzer(Fuzzer):
    def __init__(self, min_length: int = 20, max_length: int = 20,
                 char_start: int = 32, char_range: int = 32):
        self.minlen = min_length
        self.maxlen = max_length
        self.start = char_start
        self.range = char_range

    def fuzz(self):
        string_len = random.randrange(self.minlen, self.maxlen+1)
        out = ""
        for i in range(0, string_len):
            out += chr(random.randrange(self.start, self.start+self.range))
        return out
