import concurrent.futures
from simulation import Simulation


def main():
    simulation = Simulation(5, 5)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(simulation.start_simulation)
        executor.submit(simulation.listen_for_pause)


if __name__ == "__main__":
    main()
