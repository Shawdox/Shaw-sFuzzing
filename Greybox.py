import random
from html.parser import HTMLParser
import pickle
import hashlib
from typing import List, Set, Any, Tuple, Dict, Union
from Coverage import Location
from collections.abc import Sequence
from Mutation import FunctionCoverageRunner, http_program, population_coverage
from Fuzz import Fuzzer
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')


class Mutator:
    def __init__(self) -> None:
        self.mutators = [
            self.delete_random_character,
            self.insert_random_character,
            self.flip_random_character
        ]

    def insert_random_character(self, s: str) -> str:
        """Returns s with a random character inserted"""
        pos = random.randint(0, len(s))
        random_character = chr(random.randrange(32, 127))
        return s[:pos] + random_character + s[pos:]

    def delete_random_character(self, s: str) -> str:
        """Returns s with a random character deleted"""
        if s == "":
            return self.insert_random_character(s)
        pos = random.randint(0, len(s) - 1)
        return s[:pos] + s[pos + 1:]

    def flip_random_character(self, s: str) -> str:
        """Returns s with a random bit flipped in a random position"""
        if s == "":
            return self.insert_random_character(s)
        pos = random.randint(0, len(s) - 1)
        c = s[pos]
        bit = 1 << random.randint(0, 6)
        new_c = chr(ord(c) ^ bit)
        return s[:pos] + new_c + s[pos + 1:]

    def mutate(self, inp: Any) -> Any:  # can be str or Seed (see below)
        """Return s with a random mutation applied. Can be overloaded in subclasses."""
        mutator = random.choice(self.mutators)
        return mutator(inp)


class Seed:
    def __init__(self, data) -> None:
        self.data = data
        #Location = Tuple[str, int]
        self.coverage: Set[Location] = set()
        self.distance: Union[int, float] = -1
        self.energy = 0.0

    def __str__(self) -> str:
        return self.data

    __repr__ = __str__


class PowerSchedule:
    def __init__(self) -> None:
        self.path_frequency: Dict = {}

    def assignEnergy(self, population: Sequence[Seed]) -> None:
        for seed in population:
            seed.energy = 1

    def normalizedEnergy(self, population: Sequence[Seed]) -> List[float]:
        energy = list(map(lambda seed: seed.energy, population))
        sum_energy = sum(energy)
        assert sum_energy != 0
        norm_energy = list(map(lambda nrg: nrg/sum_energy, energy))
        return norm_energy

    def choose(self, population: Sequence[Seed]) -> Seed:
        """Choose weighted by normalized energy."""
        self.assignEnergy(population)
        norm_energy = self.normalizedEnergy(population)
        seed: Seed = random.choices(population, weights=norm_energy)[0]
        return seed


class AdvancedMutationFuzzer(Fuzzer):
    def __init__(self, seeds: List[str], mutator: Mutator, schedule: PowerSchedule) -> None:
        super().__init__()
        self.seeds = seeds
        self.mutator = mutator
        self.schedule = schedule
        self.inputs: List[str] = []
        self.reset()

    def reset(self) -> None:
        self.population = list(map(lambda x: Seed(x), self.seeds))
        self.seed_index = 0

    def create_candidate(self) -> str:
        seed = self.schedule.choose(self.population)
        candidate = seed.data
        trials = min(len(candidate), 1 << random.randint(1, 5))
        for i in range(trials):
            candidate = self.mutator.mutate(candidate)
        return candidate

    def fuzz(self) -> str:
        if self.seed_index < len(self.seeds):
            self.inp = self.seeds[self.seed_index]
            self.seed_index += 1
        else:
            self.inp = self.create_candidate()
        self.inputs.append(self.inp)
        return self.inp


class GreyboxFuzzer(AdvancedMutationFuzzer):
    def reset(self):
        super().reset()
        self.coverages_seen = set()
        self.population = []

    def run(self, runner: FunctionCoverageRunner) -> Tuple[Any, str]:
        result, outcome = super().run(runner)
        new_coverage = frozenset(runner.coverage())
        if new_coverage not in self.coverages_seen:
            seed = Seed(self.inp)
            seed.coverage = runner.coverage()
            self.coverages_seen.add(new_coverage)
            self.population.append(seed)
        return (result, outcome)


def getPathID(coverage):
    """Returns a unique hash for the covered statements"""
    pickled = pickle.dumps(sorted(coverage))
    return hashlib.md5(pickled).hexdigest()


class AFLFastSchedule(PowerSchedule):
    def __init__(self, exponent: float) -> None:
        super().__init__()
        self.exponent = exponent

    def assignEnergy(self, population: Sequence[Seed]) -> None:
        for seed in population:
            seed.energy = 1/(self.path_frequency[getPathID(seed.coverage)]
                             ** self.exponent)


class CountingGreyboxFuzzer(GreyboxFuzzer):
    def reset(self):
        super().reset()
        self.schedule.path_frequency = {}

    def run(self, runner: FunctionCoverageRunner) -> Tuple[Any, str]:
        result, outcome = super().run(runner)
        path_id = getPathID(runner.coverage())
        if path_id not in self.schedule.path_frequency:
            self.schedule.path_frequency[path_id] = 1
        else:
            self.schedule.path_frequency[path_id] += 1
        return (result, outcome)


class DictMutator(Mutator):
    """Variant of `Mutator` inserting keywords from a dictionary"""

    def __init__(self, dictionary: Sequence[str]) -> None:
        super().__init__()
        self.dictionary = dictionary
        self.mutators.append(self.insert_from_dictionary)

    def insert_from_dictionary(self, s: str) -> str:
        """Returns `s` with a keyword from the dictionary inserted"""
        pos = random.randint(0, len(s))
        random_keyword = random.choice(self.dictionary)
        return s[:pos] + random_keyword + s[pos:]

class MazeMutator(DictMutator):
    def __init__(self, dictionary: Sequence[str]) -> None:
        super().__init__(dictionary)
        self.mutators.append(self.delete_last_character)
        self.mutators.append(self.append_from_dictionary)

    def append_from_dictionary(self, s: str) -> str:
        """Returns s with a keyword from the dictionary appended"""
        random_keyword = random.choice(self.dictionary)
        return s + random_keyword

    def delete_last_character(self, s: str) -> str:
        """Returns s without the last character"""
        if len(s) > 0:
            return s[:-1]
        return s
    
if __name__ == '__main__':

    def crashme(s: str) -> None:
        if len(s) > 0 and s[0] == 'b':
            if len(s) > 1 and s[1] == 'a':
                if len(s) > 2 and s[2] == 'd':
                    if len(s) > 3 and s[3] == '!':
                        raise Exception()
        #crashme_runner = FunctionCoverageRunner(crashme)
        # crashme_runner.run("good")
        # print(list(crashme_runner.coverage()))
    '''
    #比较随机黑盒，变异黑盒和灰盒的区别
    seed_input = "good"
    t = 10000
    #Blackbox gen-based fuzzer
    from Fuzz import RandomFuzzer
    class RandomFuzzer(RandomFuzzer):
        def __init__(self, min_length: int = 20, max_length: int = 20, char_start: int = 32, char_range: int = 32):
            super().__init__(min_length, max_length, char_start, char_range)
            self.inputs = []
            
        def fuzz(self):
            inp = super().fuzz()
            self.inputs.append(inp)
            return inp
            
    blackbox_gen_fuzzer = RandomFuzzer(min_length=4,max_length=4,char_start=32,char_range=96)
    #Blackbox mut-based fuzzer
    blackbox_mut_fuzzer = AdvancedMutationFuzzer([seed_input],Mutator(),PowerSchedule())
    #greybox fuzzer
    greybox_fuzzer = GreyboxFuzzer([seed_input],Mutator(),PowerSchedule())
    #run 100000 times
    blackbox_gen_fuzzer.runs(FunctionCoverageRunner(crashme),t)
    blackbox_mut_fuzzer.runs(FunctionCoverageRunner(crashme),t)
    greybox_fuzzer.runs(FunctionCoverageRunner(crashme),t)
    #get coverages
    _,blackbox_gen_coverage = population_coverage(blackbox_gen_fuzzer.inputs,crashme)
    _,blackbox_mut_coverage = population_coverage(blackbox_mut_fuzzer.inputs,crashme)
    _,greybox_coverage = population_coverage(greybox_fuzzer.inputs,crashme)
    for inputs in [blackbox_gen_fuzzer.inputs,blackbox_mut_fuzzer.inputs,
                  greybox_fuzzer.inputs]:
        #print(len(inputs))
        pass
    #print(blackbox_mut_fuzzer.inputs)
    #show
    line_blackbox_gen, = plt.plot(blackbox_gen_coverage,label = "Blackbox_gen")
    line_blackbox_mut, = plt.plot(blackbox_mut_coverage,label = "Blackbox_mut")
    line_greybox, = plt.plot(greybox_coverage,label = "Greybox")
    plt.legend(handles = [line_blackbox_gen,line_blackbox_mut,line_greybox])
    plt.title('Coverage over time')
    plt.xlabel('# of inputs')
    plt.ylabel('lines covered');
    plt.show()
    '''

    """  
    #比较有无schedule分配的fuzzer的区别
    n = 10000
    seed_input = "good"
    fast_schedule = AFLFastSchedule(5)
    fast_fuzzer = CountingGreyboxFuzzer([seed_input], Mutator(), fast_schedule)
    fast_fuzzer.runs(FunctionCoverageRunner(crashme), trials=n)

    orig_schedule = PowerSchedule()
    orig_fuzzer = CountingGreyboxFuzzer([seed_input], Mutator(), orig_schedule)
    orig_fuzzer.runs(FunctionCoverageRunner(crashme),trials=n)

    import numpy as np
    x_axis = np.arange(len(fast_schedule.path_frequency))
    y_axis = list(fast_schedule.path_frequency.values())

    _, orig_coverage = population_coverage(orig_fuzzer.inputs, crashme)
    _, fast_coverage = population_coverage(fast_fuzzer.inputs, crashme)
    line_orig, = plt.plot(orig_coverage, label="Original Greybox Fuzzer")
    line_fast, = plt.plot(fast_coverage, label="Boosted Greybox Fuzzer")
    plt.legend(handles=[line_orig, line_fast])
    plt.title('Coverage over time')
    plt.xlabel('# of inputs')
    plt.ylabel('lines covered');
    plt.show() 
    """
    """ 
    def my_parser(inp: str) -> None:
        parser = HTMLParser()  # resets the HTMLParser object for every fuzz input
        parser.feed(inp)

    n = 5000
    seed_input = " "
    blackbox_fuzzer = AdvancedMutationFuzzer([seed_input],Mutator(),PowerSchedule())
    greybox_fuzzer = GreyboxFuzzer([seed_input],Mutator(),PowerSchedule())
    boosted_fuzzer = CountingGreyboxFuzzer([seed_input],Mutator(),AFLFastSchedule(5))

    blackbox_fuzzer.runs(FunctionCoverageRunner(my_parser), trials=n)
    greybox_fuzzer.runs(FunctionCoverageRunner(my_parser), trials=n)
    boosted_fuzzer.runs(FunctionCoverageRunner(my_parser), trials=n)

    _, black_coverage = population_coverage(blackbox_fuzzer.inputs, my_parser)
    _, grey_coverage = population_coverage(greybox_fuzzer.inputs, my_parser)
    _, boost_coverage = population_coverage(boosted_fuzzer.inputs, my_parser)
    line_black, = plt.plot(black_coverage, label="Blackbox Fuzzer")
    line_grey, = plt.plot(grey_coverage, label="Greybox Fuzzer")
    line_boost, = plt.plot(boost_coverage, label="Boosted Greybox Fuzzer")
    plt.legend(handles=[line_boost, line_grey, line_black])
    plt.title('Coverage over time')
    plt.xlabel('# of inputs')
    plt.ylabel('lines covered');
    #plt.show()
    print("black:{}\ngrey:{}\n".format(blackbox_fuzzer.inputs[-10:],
                                               greybox_fuzzer.inputs[-10:],
                                               ))
     """

    from Maze import generate_maze_code
    maze_string = """+-+-----+
|X|     |
| | --+ |
| |   | |
| +-- | |
|     |#|
+-----+-+"""
    maze_code = generate_maze_code(maze_string)
    with open('mycode/my_maze_code.py', 'w') as f:
        f.write(maze_code)

    
    from my_maze_code import maze
    
    from Callgraph import callgraph
    callgraph(maze_code)
    
    #print(maze(""))
    # print(maze_code)
    # print(exec(maze_code))
""" 
    #通过以下代码可以看出，没有导向的fuzzing对迷宫这种有着目标情况的效率是很低的 
    n = 2000
    seed_input = " "
    maze_fuzzer = CountingGreyboxFuzzer([seed_input],
                                        MazeMutator(list('UDLR')),
                                        AFLFastSchedule(5)
                                        )
    maze_fuzzer.runs(FunctionCoverageRunner(maze),trials = n)
    
    def print_stats(fuzzer: GreyboxFuzzer) -> None:
        total = len(fuzzer.population)
        solved = 0
        invalid = 0
        valid = 0
        for seed in fuzzer.population:
            
            s = maze(str(seed.data))
            if "INVALID" in s:
                invalid += 1
            elif "VALID" in s:
                valid += 1
            elif "SOLVED" in s:
                solved += 1
                if solved == 1:
                    print("First solution: %s" % repr(seed))
            else:
                print("??")
        print("Out of %d seeds,\
        * %4d solved the maze,\
        * %4d were valid but did not solve the maze, and\
        * %4d were invalid" % (total, solved, valid, invalid))

    print_stats(maze_fuzzer) 
    
    # Out of 413 seeds,
    #     *    0 solved the maze,
    #     *  129 were valid but did not solve the maze, and
    #     *  284 were invalid
    
    """

    
    
    

