_DEFAULT_CHANNEL_FRAME_SLICING = {
    "Green": (slice(0, 512), slice(0, 512)),
    "Red": (slice(512, 1024), slice(0, 512)),
}
_DEFAULT_CHANNEL_NAMES = tuple(_DEFAULT_CHANNEL_FRAME_SLICING.keys())
