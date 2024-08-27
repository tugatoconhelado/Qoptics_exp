import h5py
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.ticker as ticker


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
        plt.show()
    return fig

def image_from_h5(h5_path: str, save_path: str = ''):

    with h5py.File(h5_path, 'r') as f:
        data = f['Data']
        x = data['x']
        y = data['y']
        image = data['counter_image_fw']

        x = np.array(x)
        y = np.array(y)
        image = np.array(image)

    confocal_image_plot(
        image_data=image,
        x_data=x,
        y_data=y
    )

    #fig, ax = plt.subplots(figsize=(15, 5))
    #ax.imshow(image, aspect='auto', extent=[x[0], x[-1], y[0], y[-1]])
    #ax.set_xlabel('X')
    #ax.set_ylabel('Y')
    #if save_path != '':
    #    fig.savefig(save_path, dpi='figure')
    #elif save_path == '':
    #    plt.show()

if __name__=='__main__':

    imgpath = r'C:\EXP\testdata\confocal\20240725-1837-55_IMG.h5'
    image_from_h5(imgpath)