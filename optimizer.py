import numpy as np

class Optimizer:
    """
    A class that encapsulates the optimization process using a refined search for maxima
    based on a function and its derivatives. This class uses a coarse search followed by 
    a refinement process to find the optimal point of the function within a given range.
    
    Attributes:
        tolerance: float
            The tolerance for slope approximation to consider when convergence is reached.
        max_iter: int
            The maximum number of iterations for the refinement search.
    """
    
    def __init__(self, tolerance=0.001, max_iter=100):
        """
        Initializes the Optimizer with a tolerance and max iterations.
        
        Args:
            tolerance (float): The tolerance for the slope to stop the search (default is 0.001).
            max_iter (int): The maximum number of iterations for the search (default is 100).
        """
        self.tolerance = tolerance
        self.max_iter = max_iter

    def calculate_metric(self, f, alpha, *params):
        """
        Calculates the value of the objective function at a given point alpha.

        Args:
            f (callable): The function to be optimized.
            alpha (float): The input to the objective function.
            params (tuple): Additional parameters to pass to the function.

        Returns:
            float: The value of the objective function at alpha.
        """
        return f(alpha, *params)
    
    def calculate_slope(self, f, x, dx=1e-6, *params):
        """
        Calculates the slope of the objective function at a given point x using a central difference method.

        Args:
            f (callable): The function to be optimized.
            x (float): The point at which to calculate the slope.
            dx (float): The small change in x used for the central difference calculation (default is 1e-6).
            params (tuple): Additional parameters to pass to the function.

        Returns:
            float: The approximated slope of the function at x.
        """
        f_plus_dx = self.calculate_metric(f, x + dx, *params)
        f_minus_dx = self.calculate_metric(f, x - dx, *params)
        slope = (f_plus_dx - f_minus_dx) / (2 * dx)
        return slope

    def coarse_search(self, f, param_range=(0, 1), step=0.05, *params):
        """
        Performs a coarse search within a specified range to find the approximate location of the maximum.

        Args:
            f (callable): The function to be optimized.
            param_range (tuple): The range of alpha values to search over (default is (0, 1)).
            step (float): The step size for the coarse search (default is 0.05).
            params (tuple): Additional parameters to pass to the function.

        Returns:
            tuple: The left and right bounds of the interval for refinement.
        """
        best_alpha = None
        best_metric = -float('inf')
        
        # Iterate over the range with the given step size
        for alpha in np.arange(param_range[0], param_range[1], step):
            metric_value = self.calculate_metric(f, alpha, *params)
            if metric_value > best_metric:
                best_metric = metric_value
                best_alpha = alpha
        
        # Find the interval around the best alpha for refinement
        left_bound = best_alpha - step
        right_bound = best_alpha + step
        return left_bound, right_bound

    def refine_search(self, f, alpha_a, alpha_b, *params):
        """
        Refines the search for the maximum between two points using a dynamic step size 
        and slope checks to converge to the maximum.

        Args:
            f (callable): The function to be optimized.
            alpha_a (float): The left bound of the search range.
            alpha_b (float): The right bound of the search range.
            params (tuple): Additional parameters to pass to the function.

        Returns:
            float: The estimated maximum value of alpha within the range.
        """
        iteration = 0
        while iteration < self.max_iter:
            # Calculate the dynamic step size based on the distance between alpha_a and alpha_b
            dx = (alpha_b - alpha_a) / 100
            
            # Calculate slopes at points alpha_a and alpha_b
            slope_a = self.calculate_slope(f, alpha_a, dx, *params)
            slope_b = self.calculate_slope(f, alpha_b, dx, *params)
            
            # Check if both slopes are close to zero (within tolerance)
            if abs(slope_a) < self.tolerance and abs(slope_b) < self.tolerance:
                print(f"Maxima found between {alpha_a} and {alpha_b}")
                return (alpha_a + alpha_b) / 2  # Return midpoint as the max value

            # Otherwise, bisect between a and b to find the new point c
            alpha_c = (alpha_a + alpha_b) / 2
            slope_c = self.calculate_slope(f, alpha_c, dx, *params)
            
            # If the slope at c is negative, the maxima is to the left, so update the bounds to a and c
            if slope_c < 0:
                alpha_b = alpha_c
            # If the slope at c is positive, the maxima is to the right, so update the bounds to c and b
            else:
                alpha_a = alpha_c
            
            iteration += 1
        
        # If we hit max iterations without convergence
        print("Max iterations reached.")
        return (alpha_a + alpha_b) / 2  # Return midpoint as the approximate max value

    def general_search(self, f, param_range=(0, 1), step=0.05, *params):
        """
        Perform a full search for the optimal point using a coarse search followed by refinement.

        Args:
            f (callable): The function to be optimized.
            param_range (tuple): The range of alpha values to search over (default is (0, 1)).
            step (float): The step size for the coarse search (default is 0.05).
            params (tuple): Additional parameters to pass to the function.

        Returns:
            float: The optimal value of alpha based on the objective function.
        """
        # Perform the coarse search to get an initial guess for the optimal region
        alpha_a, alpha_b = self.coarse_search(f, param_range, step, *params)
        
        # Refine the search within the bounds found by the coarse search
        return self.refine_search(f, alpha_a, alpha_b, *params)


# Example Function (f(x) that you want to optimize)
def example_function(x):
    """
    Example quadratic function with a maximum at x = 0.5.
    """
    return -(x - 0.5)**2 + 1

# Example Usage:

# Instantiate the Optimizer with the necessary parameters
optimizer = Optimizer(tolerance=0.001, max_iter=100)

# Perform the general search to find the optimal point
best_alpha = optimizer.general_search(example_function, param_range=(0, 1), step=0.05)

print(f"Best Alpha: {best_alpha}")

