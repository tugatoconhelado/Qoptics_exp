from scipy.optimize import curve_fit
import numpy as np


def gaussian(x: np.ndarray, a: float, x0: float, sigma: float, background: float) -> np.ndarray:
    """
    Gaussian function.

    Parameters
    ----------
    x : np.ndarray
        x values of the gaussian
    a : float
        Amplitude of the gaussian
    x0 : float
        Mean of the gaussian
    sigma : float
        Standard deviation of the gaussian

    Returns
    -------
    np.ndarray
        Gaussian function evaluated at x
    """
    return a * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2)) + background


def fit_gaussian(x: np.ndarray, y: np.ndarray) -> tuple:
    """
    Fits a gaussian to a given x, y curve.

    Parameters
    ----------
    x : np.ndarray
        x values of the data
    y : np.ndarray
        y values of the data

    Returns
    -------
    tuple
        Tuple containing the parameters of the gaussian fit
    """
    # Initial guess for the gaussian parameters
    p0 = (np.max(y), x[np.argmax(y)], np.std(x), np.min(y))
    
    # Fit the gaussian
    try:
        popt, pocv = curve_fit(gaussian, x, y, p0=p0)
    except RuntimeError:
        popt = p0
        pocv = (None, None, None, None)

    return (popt, pocv)


if __name__ == '__main__':

    import matplotlib.pyplot as plt

    x = np.linspace(-2, 2, 500)
    y = gaussian(x, 1, 0, 0.3, 100) + np.random.normal(0, 0.1, 500) + 100

    yfit = gaussian(x, *fit_gaussian(x, y)[0])

    plt.plot(x, y, color='blue')
    plt.plot(x, yfit, color='red')
    plt.show()

    