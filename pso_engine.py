import random

class Particle:
    def __init__(self, possible_routes, w_cost, w_time):
        # Select a random initial route from all possible paths (the Search Space)
        self.position = random.choice(possible_routes)
        self.pBest = self.position
        self.w_cost = w_cost
        self.w_time = w_time
        self.pBest_fitness = self.calculate_fitness(self.pBest)

    def calculate_fitness(self, route):
        # Applies the Fitness Function: F = (w1 * C) + (w2 * T)
        # (Distance is omitted here since our DB mesh uses predefined landmarks)
        total_cost = sum(float(leg['cost']) for leg in route)
        total_time = sum(float(leg['travel_time']) for leg in route)
        
        # A lower fitness score represents a more optimal route (Minimization)
        return (self.w_cost * total_cost) + (self.w_time * total_time)

def run_pso(possible_routes, mode, num_particles=30, iterations=50):
    if not possible_routes:
        return None

    # Apply Dynamic Weights based on user optimization preference
    if mode == 'economic':
        w_cost, w_time = 0.8, 0.2  # Prioritizes lower transport fares
    elif mode == 'express':
        w_cost, w_time = 0.2, 0.8  # Prioritizes speed and directness
    else:
        w_cost, w_time = 0.5, 0.5  # Balanced Mode

    # Initialize Swarm
    swarm = [Particle(possible_routes, w_cost, w_time) for _ in range(num_particles)]
    
    # Determine initial gBest (Global Best)
    gBest = swarm[0].position
    gBest_fitness = swarm[0].calculate_fitness(gBest)

    # Find the best starting point among the swarm
    for p in swarm:
        if p.pBest_fitness < gBest_fitness:
            gBest = p.pBest
            gBest_fitness = p.pBest_fitness

    # The PSO Convergence Loop
    for _ in range(iterations):
        for particle in swarm:
            # Stochastic exploration vs Exploitation
            if random.random() < 0.3:
                # Explore: Try a random route from the search space
                candidate_route = random.choice(possible_routes)
            else:
                # Exploit: Move towards the Global Best
                candidate_route = gBest 
            
            candidate_fitness = particle.calculate_fitness(candidate_route)

            # Update Personal Best (Cognitive Influence)
            if candidate_fitness < particle.pBest_fitness:
                particle.pBest = candidate_route
                particle.pBest_fitness = candidate_fitness

            # Update Global Best (Social Influence)
            if candidate_fitness < gBest_fitness:
                gBest = candidate_route
                gBest_fitness = candidate_fitness

    # Construct the final itinerary
    return {
        'route': gBest,
        'fitness_score': gBest_fitness,
        'total_cost': sum(float(leg['cost']) for leg in gBest),
        'total_time': sum(int(leg['travel_time']) for leg in gBest)
    }