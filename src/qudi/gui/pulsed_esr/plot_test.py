import pyqtgraph as pg

pg.mkQApp()

plot = pg.PlotWidget()
moving_item = pg.TextItem("Moving", anchor=(0.5, 0.5))
still_item = pg.TextItem("Still", anchor=(0.5, 0.5))

still_item.setFlag(still_item.GraphicsItemFlag.ItemIgnoresTransformations)
# ^^^ This line is necessary

plot.addItem(moving_item, ignoreBounds=True)
# Use this instead of `plot.addItem`
still_item.setParentItem(plot.plotItem)

# This position will be in pixels, not scene coordinates since transforms are ignored.
# You can use helpers like `mapFromScene()` etc. to translate between pixels
# and viewbox coordinates
still_item.setPos(300, 300)

plot.show()

pg.exec()