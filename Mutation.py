from typing import Tuple, List, Callable, Set, Any
from urllib.parse import urlparse
from Fuzz import Fuzzer,Runner
from Coverage import Coverage,population_coverage,Location
import random
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

class MutationFuzzer(Fuzzer):
    """Base class for mutational fuzzing"""

    def __init__(self, seed: List[str],
                 min_mutations: int = 2,
                 max_mutations: int = 10) -> None:
        """Constructor.
        `seed` - a list of (input) strings to mutate.
        `min_mutations` - the minimum number of mutations to apply.
        `max_mutations` - the maximum number of mutations to apply.
        """
        self.seed = seed
        self.min_mutations = min_mutations
        self.max_mutations = max_mutations
        self.reset()

    def reset(self) -> None:
        """Set population to initial seed.
        To be overloaded in subclasses."""
        self.population = self.seed
        self.seed_index = 0

class FunctionRunner(Runner):
    def __init__(self,function:Callable) -> None:
        self.function = function
    
    def run_function(self,inp:str):
        return self.function(inp)
    
    def run(self,inp:str):
        try:
            result = self.run_function(inp)
            outcome = self.PASS
        except Exception:
            result = None
            outcome = self.FAIL
        return result,outcome
    

class FunctionCoverageRunner(FunctionRunner):
    def run_function(self, inp: str) -> Any:
        with Coverage() as cov:
            try:
                result = super().run_function(inp)
            except Exception as exc:
                self._coverage = cov.coverage()
                raise exc

        self._coverage = cov.coverage()
        return result

    def coverage(self) -> Set[Location]:
        return self._coverage


def delete_random_character(s: str) -> str:
        """Returns s with a random character deleted"""
        if s == "":
            return s

        pos = random.randint(0, len(s) - 1)
        # print("Deleting", repr(s[pos]), "at", pos)
        return s[:pos] + s[pos + 1:]

def insert_random_character(s: str) -> str:
    """Returns s with a random character inserted"""
    pos = random.randint(0, len(s))
    random_character = chr(random.randrange(32, 127))
    # print("Inserting", repr(random_character), "at", pos)
    return s[:pos] + random_character + s[pos:]

def flip_random_character(s):
    """Returns s with a random bit flipped in a random position"""
    if s == "":
        return s

    pos = random.randint(0, len(s) - 1)
    c = s[pos]
    bit = 1 << random.randint(0, 6)
    new_c = chr(ord(c) ^ bit)
    #print("Flipping", bit, "in", repr(c) + ", giving", repr(new_c))
    return s[:pos] + new_c + s[pos + 1:]

def mutate(s: str) -> str:
    """Return s with a random mutation applied"""
    mutators = [
        delete_random_character,
        insert_random_character,
        flip_random_character
    ]
    mutator = random.choice(mutators)
    # print(mutator)
    return mutator(s)

def http_program(url: str) -> bool:
    supported_schemes = ["http", "https"]
    result = urlparse(url)
    if result.scheme not in supported_schemes:
        raise ValueError("Scheme must be one of " +
                        repr(supported_schemes))
    if result.netloc == '':
        raise ValueError("Host must be non-empty")

    # Do something with the URL
    return True

#向类中添加函数
class MutationFuzzer(MutationFuzzer):
    def mutate(self,inp:str):
        return mutate(inp)

class MutationFuzzer(MutationFuzzer):
    def create_candidate(self) -> str:
        """Create a new candidate by mutating a population member"""
        candidate = random.choice(self.population)
        trials = random.randint(self.min_mutations, self.max_mutations)
        for i in range(trials):
            candidate = self.mutate(candidate)
        return candidate

class MutationFuzzer(MutationFuzzer):
    def fuzz(self) -> str:
        if self.seed_index < len(self.seed):
            # Still seeding
            self.inp = self.seed[self.seed_index]
            self.seed_index += 1
        else:
            # Mutating
            self.inp = self.create_candidate()
        return self.inp

class MutationCoverageFuzzer(MutationFuzzer):
    """Fuzz with mutated inputs based on coverage"""

    def reset(self) -> None:
        super().reset()
        self.coverages_seen: Set[frozenset] = set()
        # Now empty; we fill this with seed in the first fuzz runs
        self.population = []

    def run(self, runner: FunctionCoverageRunner) -> Any:
        """Run function(inp) while tracking coverage.
           If we reach new coverage,
           add inp to population and its coverage to population_coverage
        """
        result, outcome = super().run(runner)
        new_coverage = frozenset(runner.coverage())
        if outcome == Runner.PASS and new_coverage not in self.coverages_seen:
            # We have new coverage
            self.population.append(self.inp)
            self.coverages_seen.add(new_coverage)

        return result

if __name__ == '__main__':

    '''
    http_runner = FunctionCoverageRunner(http_program)
    seed_input = "http://www.google.com/search?q=fuzzing"
    mutation_fuzzer = MutationCoverageFuzzer(seed=[seed_input])
    mutation_fuzzer.runs(http_runner, trials=10000)
    #print(mutation_fuzzer.population)
    all_coverage, cumulative_coverage = population_coverage(
        mutation_fuzzer.population, http_program)
    plt.plot(cumulative_coverage)
    plt.title('Coverage of urlparse() with random inputs')
    plt.xlabel('# of inputs')
    plt.ylabel('lines covered');
    plt.show()
    '''

    #Exercise 1
    from Coverage import cgi_decode
    seed = ['Hellow World']
    cgi_runner = FunctionCoverageRunner(cgi_decode)
    cgi_fuzzer = MutationCoverageFuzzer(seed = seed)
    results = cgi_fuzzer.runs(cgi_runner,10000)
    print(cgi_fuzzer.population) 
    print(cgi_runner.coverage())
    all_coverage, cumulative_coverage = population_coverage(
        cgi_fuzzer.population, cgi_decode)
    plt.plot(cumulative_coverage)
    plt.title('Coverage of cgi_decode() with random inputs')
    plt.xlabel('# of inputs')
    plt.ylabel('lines covered');
    plt.show()
    
    #Exercise 2
    from Fuzz import ProgramRunner
    seed = ["2 + 2"]
    bc = ProgramRunner(program="bc")
    m = MutationFuzzer(seed)
    outcomes = m.runs(bc,100)
    

