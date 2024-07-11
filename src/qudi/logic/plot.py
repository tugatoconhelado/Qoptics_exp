import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.ticker as ticker

matplotlib.rcdefaults()
try:
    plt.style.use('presentation')
except Exception as e:
    print(e)

matplotlib.use('Qt5Agg')

def confocal_image_plot(
        image_data : np.ndarray, x_data : np.ndarray, y_data : np.ndarray,
        save_path : str = '') -> matplotlib.figure.Figure:
    """
    Creates a heatmap image with scalebar obtained from x_data and y_data

    It saves the image to `save_path`. The scalebar is made to have a constant
    size and represent 20% of the image total size on the x axis. The colorbar
    represents the data on the image, but has a scaling of 1 / 1000 to display
    the units in kcounts instead of counts.

    Parameters
    ----------
    image_data : np.ndarray
        2D array containing the image data
    x_data : np.ndarray
        Array containing the x axis values of each pixel
    y_data : np.ndarray
        Array containing the y axis values of each pixel
    save_path : str
        Path to save the image to.
    
    Returns
    -------
    fig : matplotlib.figure.Figure
        The Figure created containing the image.
    """

    pixels = (len(image_data[0]), len(image_data))
    fig, ax = plt.subplots()
    im = ax.imshow(image_data / 1000, origin='lower') # Converts to kcts

    color_bar = ax.figure.colorbar(im, ax=ax, format='%1i')
    color_bar.ax.set_ylabel("Intensity (kcts/sec)", rotation=-90, va='bottom')

    ax.set_xticks([])
    ax.set_yticks([])

    range_x = np.max(x_data) - np.min(x_data)
    range_y = np.max(y_data) - np.min(y_data)

    size_per_pixel = range_x / pixels[0]
    scalebar_size = pixels[0] / 5
    scalebar_size_str = round(size_per_pixel * scalebar_size, 1)
    scalebar = AnchoredSizeBar(
        transform=ax.transData,
        size=scalebar_size,
        label=f'{scalebar_size_str} $\mu m$',
        loc='lower right',
        pad=1,
        color='white',
        frameon=False,
        size_vertical=float(pixels[0] / 140)
    )
    ax.add_artist(scalebar)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    if save_path != '':
        fig.savefig(save_path, dpi='figure')
    elif save_path == '':
        fig.show()
    return fig

def spectrum_plot(
        x_data : np.ndarray, intensity : np.ndarray,
        save_path : str = '') -> matplotlib.figure.Figure:
    """
    Creates a plot of `x_data` versus `intensity`.

    Sets labels based on unit (TO BE IMPLEMENTED). Modifies the number of major
    and minor ticks. Creates range frames to the max an min values of x and y
    axis.

    Parameters
    ----------
    x_data : np.ndarray
        Array containing the data to be displayed on the x axis
    intensity : np.ndarray
        Array containing the data of the intensity of the spectrum, it is
        displyed on the y axis.
    units : str
        Units for the x axis
    save_path : str
        Path to save the image
    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure containing the plot.
    """
    x = x_data
    y = intensity
    fig, ax = plt.subplots()

    ax.plot(x, y)

    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Intensity\n(counts)', rotation=0, labelpad=40, ha='left', y=0.9)

    # Set number of minor and major ticks
    ax.xaxis.set_major_locator(ticker.MaxNLocator(5))
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(3))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    
    # Range frames
    #ax.spines['bottom'].set_bounds(min(x), max(x))
    #ax.spines['left'].set_bounds(min(y), max(y))

    if save_path != '':
        fig.savefig(save_path, dpi='figure')
    elif save_path == '':
        fig.show()
    return fig

def timetrace_plot(
        x_data : np.ndarray, counts : np.ndarray,
        save_path : str = '') -> matplotlib.figure.Figure:
    """
    Creates a plot of `x_data` versus `counts`.

    Sets labels based on unit (TO BE IMPLEMENTED). Modifies the number of major
    and minor ticks. Creates range frames to the max an min values of x and y
    axis.

    Parameters
    ----------
    x_data : np.ndarray
        Array containing the data to be displayed on the x axis
    counts : np.ndarray
        Array containing the data of the counts of the spectrum, it is
        displyed on the y axis.
    units : str
        Units for the x axis
    save_path : str
        Path to save the image
    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure containing the plot.
    """
    x = x_data
    y = counts
    fig, ax = plt.subplots(figsize=(15, 5))

    ax.plot(x, y, '-')

    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Intensity\n(cps)', rotation=0, labelpad=40, ha='left', y=0.9)

    # Set number of minor and major ticks
    ax.xaxis.set_major_locator(ticker.MaxNLocator(5))
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(3))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    
    # Range frames
    #ax.spines['bottom'].set_bounds(min(x), max(x))
    #ax.spines['left'].set_bounds(min(y), max(y))

    if save_path != '':
        fig.savefig(save_path, dpi='figure')
    #elif save_path == '':
    #    fig.show()
    return fig

def lifetime_plot(
        x_data : np.ndarray, counts : np.ndarray,
        save_path : str = '') -> matplotlib.figure.Figure:
    """
    Creates a plot of `x_data` versus `counts`.

    Sets labels based on unit (TO BE IMPLEMENTED). Modifies the number of major
    and minor ticks. Creates range frames to the max an min values of x and y
    axis.

    Parameters
    ----------
    x_data : np.ndarray
        Array containing the data to be displayed on the x axis
    counts : np.ndarray
        Array containing the data of the counts of the spectrum, it is
        displyed on the y axis.
    units : str
        Units for the x axis
    save_path : str
        Path to save the image
    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure containing the plot.
    """
    x = x_data
    y = counts
    fig, ax = plt.subplots(figsize=(15, 5))

    ax.plot(x, y, '-')

    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Counts', rotation=0, labelpad=40, ha='left', y=0.9)

    # Set number of minor and major ticks
    ax.xaxis.set_major_locator(ticker.MaxNLocator(5))
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(3))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    
    # Range frames
    #ax.spines['bottom'].set_bounds(min(x), max(x))
    #ax.spines['left'].set_bounds(min(y), max(y))

    if save_path != '':
        fig.savefig(save_path, dpi='figure')
    elif save_path == '':
        fig.show()
    return fig


if __name__ == '__main__':
    import json
    imgpath = os.path.join('data', 'confocal', 'IMG2023-08-04_15-46-54.json')
    with open(imgpath, 'r') as file:
        data = json.load(file)
    data = data['Experiment_Data']
    print(data.keys())
    img = confocal_image_plot(
        image_data=np.array(data['counter_image_fw']),
        x_data=np.array(data['x']),
        y_data=np.array(data['y']),
        save_path='imgetest.png'
    )

    sprpath = os.path.join('data', 'spectra', 'SPR2023-10-08_15-23-46.json')
    with open(sprpath, 'r') as file:
        data = json.load(file)
    data = data['Experiment_Data']
    print(data.keys())
    sprimg = spectrum_plot(
        x_data=data['wavelength'],
        intensity=data['spectrum'],
        units='Wavelength (nm)'#,
        #save_path='sprtest.png'
    )
