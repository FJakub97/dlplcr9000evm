import numpy as np
from numpy.typing import NDArray
import os
from PIL import Image


def load_bitmap_image(file_path: str, file_name: str) -> NDArray[np.uint8]:
    with Image.open(os.path.join(file_path, file_name)) as bitmap_image:
        return np.asarray(bitmap_image, dtype=np.uint8)


def merge_bitmap_images(bitmap_images: list[NDArray]) -> list[NDArray]:
    merged_images = []

    batch_size = 24
    number_of_channels = 3
    number_of_batches = (len(bitmap_images) + batch_size - 1) // batch_size

    for batch_number in range(number_of_batches):
        merged_image = np.zeros(
            (bitmap_images[0].shape[0], bitmap_images[0].shape[1], number_of_channels),
            dtype=np.uint8,
        )
        batch_images = bitmap_images[(batch_number * batch_size) : ((batch_number + 1) * batch_size)]

        for bit_position, batch_image in enumerate(batch_images):
            if bit_position < 8:
                merged_image[:, :, 2] |= batch_image << bit_position
            elif bit_position < 16:
                merged_image[:, :, 1] |= batch_image << (bit_position - 8)
            else:
                merged_image[:, :, 0] |= batch_image << (bit_position - 16)

        merged_images.append(merged_image)

    return merged_images


if __name__ == "__main__":
    pass
