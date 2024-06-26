import numpy as np
import math
import statistics as stats
from colorama import Fore
import matplotlib.pyplot as plt

# This code is open source. Feel free to use and modify with credit to the original repository

########## Isochron age method ##########

Rb_lambda = 1.42e-11

# Age to display - Double
def compute_Isochron(York, decay_const):
    slope = York['slope']
    slope_uncertainty = York['slope_err']
    
    # Simple partial derivative error propogation
    def propogate_age_uncertainty(slope, slope_uncertainty):
        # Partial derivative w/ respect to slope
        slope_uncertainty_squared = slope_uncertainty**2
        partial_derivative_squared_slope = (1 / (decay_const * (slope + 1)))**2 
        return math.sqrt(slope_uncertainty_squared * partial_derivative_squared_slope) / 1e6

    # Handle the corner Case
    if (slope == 0):
        raise Exceptions("Illigal slope argument")
    age = ((math.log(1 + slope)) / (decay_const)) / 1e6
    
    age_uncertainty = propogate_age_uncertainty(slope, slope_uncertainty)
    
    fancify_on_return = {'age': age, 'age_err': age_uncertainty, 'Sr_intercept': York['intercept'], 'Sr_intercept_err': York['intercept_err']}
    return fancify_on_return


########## York-Fit complete regression code ##########

def York_Fit(x, y, x_unsc, y_unsc, binitial, iterator):
    
    ######### for unsc ##########
    def computeUncertanties(alpha_array, Z_array, X_m, Y_m, U_array, V_array, x_weights, y_weights, r, b, a, MSWD_term, x, y):
        # Vars for convenience and other stuff from lecture that I don't end up using
        iterator = len(alpha_array)
        b_prime = []
        u_array = []
        v_array = []
        x_m = 0
        y_m = 0

        # This cchunk just sets all vars from ^
        for i in range(iterator):
            index = ((Z_array[i]) * ((U_array[i]/y_weights[i]) + ((b * V_array[i])/(x_weights[i])) - (((b*U_array[i]) + V_array[i]) * (r/alpha_array[i]))))
            b_prime.append(index)

        for i in range(iterator):
            u_array.append(X_m + b_prime[i])
            v_array.append(Y_m + (b_prime[i] * b))
        numer = 0
        denom = 0
        for i in range(iterator):
            numer = numer + (Z_array[i] * u_array[i])
            denom = denom + Z_array[i]
        x_m = numer / denom
        numerator = 0
        denominator = 0
        for i in range(iterator):
            numerator = numerator + (Z_array[i] * v_array[i])
            denominator = denominator + Z_array[i]
        y_m = numerator / denominator

        # The actual uncertainties -- I use the method from Faure and Mensing, had lots of problems w/ the lecture slides.
        # Like, i'm sure thier right, but I just couln't seem to figure out the code
        b_unsc_denom = 0
        a_unsc_denom = 0
        a_unsc_numer = 0
        for i in range(iterator):
            b_unsc_denom = b_unsc_denom + (Z_array[i] * ((u_array[i] - x_m)**2))
            a_unsc_denom = a_unsc_denom + Z_array[i]
        b_unsc_squared = 1 / (b_unsc_denom)
        a_unsc_squared = (1/a_unsc_denom) + (b_unsc_squared*(x_m**2))

        # Degrees of freedom for linear fit
        deg_free = iterator - 2
        MSWD = (1/deg_free) * MSWD_term

        return math.sqrt(b_unsc_squared), math.sqrt(a_unsc_squared), MSWD

    ####################################
    
    ######### to Preprocess ##########
    # Calculate the oodles of subsets and massaged data needed for York
    def preproccess(x, y, x_unsc, y_unsc, b):

        # corner case
        if (len(x) != len(y) or len(x_unsc) != len(y_unsc)) :
            raise Exception(Fore.RED + "array lengths not compatable for York Fit")

        # Just for convenience
        iterable = len(x)

        # Define the weighting facors -- Consider that Python treats np.array as a hash table or perhaps a LL
        x_stdev, y_stdev = stats.stdev(x), stats.stdev(y)
        x_weights, y_weights = [], []
        for i in range(iterable):
            x_weights.append(1 / (x_unsc[i] ** 2))
            y_weights.append(1 / (y_unsc[i] ** 2))

        # Define r as the correlation coefficient of the error arrays
        xerrmean, yerrmean = stats.mean(x_unsc), stats.mean(y_unsc)
        temp_num, temp_denom, temp_denomT1, temp_denomT2 = 0, 0, 0, 0
        for i in range(iterable):
            temp_num = temp_num + ((x_unsc[i] - xerrmean) * (y_unsc[i] - yerrmean))
            temp_denomT1 = temp_denomT1 + ((x_unsc[i] - xerrmean) ** 2)
            temp_denomT2 = temp_denomT2 + ((y_unsc[i] - yerrmean) ** 2)
        temp_denom = math.sqrt(temp_denomT1) * math.sqrt(temp_denomT2)
        r = temp_num / temp_denom


        # Define the alpha array and other stuff
        alpha_array, Z_array, X_m, Y_m, U_array, V_array= [], [], 0, 0, [], []
        for i in range(iterable):
            alpha_array.append(math.sqrt(x_weights[i] * y_weights[i]))
        for i in range(iterable):
            Z_array.append((x_weights[i] * y_weights[i]) / (((b**2) * y_weights[i]) + (x_weights[i]) - (2 * b * r * alpha_array[i])))

        temp_num, temp_denom = 0, 0
        for i in range(iterable):
            temp_num = temp_num + (Z_array[i] * x[i])
            temp_denom = temp_denom + Z_array[i]
        X_m = temp_num / temp_denom

        temp_num, temp_denom = 0, 0
        for i in range(iterable):
            temp_num = temp_num + (Z_array[i] * y[i])
            temp_denom = temp_denom + Z_array[i]
        Y_m = temp_num / temp_denom

        for i in range(iterable):
            U_array.append(x[i] - X_m)
            V_array.append(y[i] - Y_m)

        return alpha_array, Z_array, X_m, Y_m, U_array, V_array, x_weights, y_weights, r

    ###############################
    
    ######### to get MSWD #########
    
    def Compute_MSWD(x, y, x_unsc, y_unsc, a, b, Z_array):
        term = 0
        for i in range(len(x)):
            # MSWD_numerator = (y[i] - a - (b*x[i]))**2
            # MSWD_denominator = (y_unsc[i]**2) + ((b**2) * (x_unsc[i]**2))
            # term = term + (MSWD_numerator / MSWD_denominator)
            term = term + (Z_array[i]*((y[i] - (b*x[i]) - a)**2))
        return term
    
    ###############################
    
    # CAN RETURN RESULTS WICH SEEM ACCURATE BUT ARE NOT IF A GOOD GUESS IS NOT PASSED
    b = binitial
    york_guess = 0
    
    # Handle the corner case
    if (iterator <= 0):
        raise Exceptions(Fore.RED + "Catch Infinite lopp: iterator must be non-zero")
    
    ratios = []
    slopes = []
    
    # The meat
    while(b != york_guess):
        
        # Preprocess the passed data and retrieve necessary arrays
        alpha_array, Z_array, X_m, Y_m, U_array, V_array, x_weights, y_weights, r = preproccess(x, y, x_unsc, y_unsc, b)
        temp_num, temp_denom = 0, 0
        
        # Checking for most acurate slope
        for i in range(len(alpha_array)):
            temp_num = temp_num + (((Z_array[i]**2) * V_array[i]) * ((U_array[i]/y_weights[i]) + ((b * V_array[i])/(x_weights[i])) - (((b*U_array[i]) + V_array[i]) * (r/alpha_array[i]))))
            temp_denom = temp_denom + (((Z_array[i]**2) * U_array[i]) * ((U_array[i]/y_weights[i]) + ((b * V_array[i])/(x_weights[i])) - (((b*U_array[i]) + V_array[i]) * (r/alpha_array[i]))))
        york_guess = temp_num / temp_denom
        low = b - (b*0.005)
        high = b + (b*0.005)
        
        # return the closest matching slope (minimize the ratio of b/york_guess)
        # RIP my computer, i'm so sorry but I don't care to optimize this code
        best_ratio = 10000
        best_slope = 0
        get_ratioed = abs(1 - abs(york_guess/b))
        ratios.append(get_ratioed)
        slopes.append(york_guess)
        
        b = b + iterator

        # This can be changed for the specific isochron
        if (b > 0.014):
            break
            
    best_index = ratios.index(min(ratios))
    best_slope = slopes[best_index]
    # Ensure that we have these updated for the best slope val
    alpha_array, Z_array, X_m, Y_m, U_array, V_array, x_weights, y_weights, r = preproccess(x, y, x_unsc, y_unsc, best_slope)
    intercept = Y_m - (best_slope * X_m)
    
    # This is where things get funky
    MSWD_term = Compute_MSWD(x, y, x_unsc, y_unsc, intercept, best_slope, Z_array)
    slope_fit_err, intercept_fit_err, MSWD = computeUncertanties(alpha_array, Z_array, X_m, Y_m, U_array, V_array, x_weights, y_weights, r, best_slope, intercept, MSWD_term, x, y)

    fancify_on_return = {'slope': best_slope, 
                         'slope_err': slope_fit_err,
                         'intercept': intercept,
                         'intercept_err': intercept_fit_err,
                         'MSWD': MSWD,
                         'x': x,
                         'y': y,
                         'x_err': x_unsc,
                         'y_err': x_unsc}
    return fancify_on_return


def unpack(fancify_on_return):
    # Upack York fit data
    if (len(fancify_on_return) > 5):
        print(Fore.GREEN +"Linear York Fit best slope: ", fancify_on_return['slope'], "\nLinear York Fit best intercept: ", fancify_on_return['intercept'], "\nBest Fit Slope Uncertainty: ", fancify_on_return['slope_err'], "\nBest Fit Intercept Uncertainty: ", fancify_on_return['intercept_err'], "\nMSWD: ", fancify_on_return['MSWD'])
    # unpack Isochron Info
    else:
        print(Fore.GREEN + "\n\nIsochron Info:", "\nIsochron Age (Ma): ", fancify_on_return['age'], " +- ", fancify_on_return['age_err'], "\n87Sr/86Sr_initial intercept: ", fancify_on_return['Sr_intercept'], " +- ", fancify_on_return['Sr_intercept_err'])


        # Plot the isochron data
def plot_isoc(York):
    import matplotlib.pyplot as plt
    x = York['x']
    y = York['y']
    x_err = York['x_err']
    y_err = York['y_err']
    # Plot the data with approproate errors
    plt.scatter(np.array(x), np.array(y), s = 7)
    plt.errorbar(np.array(x), np.array(y), yerr=y_err, xerr=x_err, linestyle=' ', capsize=5)
    x_vals = np.array(x)
    y_vals = (x_vals * York['slope']) + York['intercept']
    plt.plot(x_vals, y_vals, label="Linear York Fit")
    
    # Make the graph look pretty
    plt.xlabel('87Rb/86Sr')
    plt.ylabel('87Sr/86Sr')
    plt.title("Rb/Sr Isochron Plot")
    plt.legend()

    # Show plot
    plt.show()
    
# Take in the data, run the york fit and propograte uncertainties
# For unit testing. This method shouldn't be called
def main():
    x = [131.8, 0.21, 1.64, 0.3, 0.89, 145.5, 0.004, 0.66, 0.22, 0.006, 0.28, 142, 0.05, 0.13, 0.66, 0.84, 0.12, 0.57]
    y = [0.86108, 0.70593, 0.70764, 0.70622, 0.70667, 0.88108, 0.70572, 0.70664, 0.70607, 0.70585, 0.70612, 0.86919, 
         0.70652, 0.70651, 0.70724, 0.70745, 0.70662, 0.70717]
    x_err = [1.318, 0.0021, 0.0164, 0.003, 0.0089, 1.455, 0.00004, 0.0066, 0.0022, 0.00006, 0.0028, 1.42, 0.0005, 0.0013, 
             0.0066, 0.0084, 0.0012, 0.0057]
    y_err = [0.00014, 0.00014, 0.00021, 0.00016, 0.00022, 0.0002, 0.00019, 0.00016, 0.0002, 0.00024, 0.0002, 0.00022, 
             0.00025, 0.00013, 0.00016, 0.00019, 0.00017, 0.00017]
    
    
    # The important stuff from York fit
    York = York_Fit(x, y, x_err, y_err, binitial = 0.0001, iterator = 0.000005)
    unpack(York)
    
    # This is simple math
    Isochron = compute_Isochron(York, Rb_lambda)
    unpack(Isochron)
    
    plot_isoc(x, y, x_err, y_err, York)