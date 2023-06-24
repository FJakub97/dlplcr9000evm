import os
from dlplcr9000evm import load_bitmap_image, merge_bitmap_images, encode_erle, DLPC900Controller, DLPLCR9000EVM

# Due to memory limitations of attachments, it is necessary to download sample examples from the manufacturer's website.
    # 1. Download: https://www.ti.com/tool/DLPC900REF-SW
    # 2. Install the downloaded .exe file
    # 3. Locate the folder where the images are: C:\Texas Instruments-DLP\DLPC900REF-SW-5.1.0\DLPC900REF-SW-5.1.0\DLPC900REF-GUI\Images and Batch files\LCR9000_Images
    # 4. Move these images from the folder mentioned above to folder bitmap_images
bitmap_images = [load_bitmap_image(os.path.join(os.getcwd(), "bitmap_images"), f"{i}_Binary.bmp") for i in range(400)]

# Converting bitmap images to 24-bit images (this is done in batches of 24 bitmap images)
merged_images = merge_bitmap_images(bitmap_images)

# Splitting the images into left and right halves, because the evaluation module contains two chips and each controls one half of the DMD.
primary_merged_images = [merged_image[0:1600, 0:1280, :] for merged_image in merged_images]
secondary_merged_images = [merged_image[0:1600, 1280:2560, :] for merged_image in merged_images]

# Compression of split 24-bit images.
encoded_primary_images_data = [encode_erle(primary_merged_image) for primary_merged_image in primary_merged_images]
encoded_secondary_images_data = [
    encode_erle(secondary_merged_image) for secondary_merged_image in secondary_merged_images
]
# Images are uploaded to DLPC900 in reverse order.
encoded_primary_images_data.reverse()
encoded_secondary_images_data.reverse()

# Mapping the order of uploaded images to the order of patterns in the sequence (in this case it is the same).
pattern_indexes = [pattern_index for pattern_index in range(len(bitmap_images))]

# Define pattern exposure in microseconds and dark display time also in microseconds for each pattern.
pattern_exposures_in_microseconds = [5000] * len(pattern_indexes)
dark_display_times_in_microseconds = [0] * len(pattern_indexes)

# Initializes DLPLCR9000EVM class and perform connection to the DLP LightCrafter 9000 EVM.
lightcrafter = DLPLCR9000EVM()
lightcrafter.connect()

# Before you want to load a new LUT pattern definition, LUT configuration, or new images, you must stop the currently running pattern sequence.
lightcrafter.set_pattern_display_control(0)

# Selecting mode Pattern On-The-Fly
lightcrafter.set_pattern_display_mode(3)

# Load the LUT definition for every pattern (for every bitmap image)
for pattern_index in pattern_indexes:
    image_pattern_index = pattern_index // 24
    bit_position = pattern_index - image_pattern_index * 24
    lightcrafter.set_pattern_display_lut_definition(
        pattern_index,
        pattern_exposures_in_microseconds[pattern_index],
        True,
        1,
        7,
        False,
        dark_display_times_in_microseconds[pattern_index],
        False,
        False,
        image_pattern_index,
        bit_position,
    )

# Specify the LUT configuration. NOTE: When last argument of this method is set to 0, it means repeat patterns.
lightcrafter.set_pattern_display_lut_configuration(len(pattern_indexes), 0)

# Perform initialization and loading of the compressed images data to DLPC900.
for image_index, (encoded_primary_image_data, encoded_secondary_image_data) in enumerate(
    zip(encoded_primary_images_data, encoded_secondary_images_data)
):
    image_index = len(primary_merged_images) - image_index - 1
    lightcrafter.initialize_pattern_bmp_load(DLPC900Controller.PRIMARY, image_index, len(encoded_primary_image_data))
    lightcrafter.initialize_pattern_bmp_load(
        DLPC900Controller.SECONDARY, image_index, len(encoded_secondary_image_data)
    )
    lightcrafter.pattern_bmp_load(DLPC900Controller.PRIMARY, encoded_primary_image_data)
    lightcrafter.pattern_bmp_load(DLPC900Controller.SECONDARY, encoded_secondary_image_data)

while True:
    pattern_display_action = input("Select pattern display action - 'start', 'stop', 'pause', or end experiment by 'end':")
    match pattern_display_action.lower():
        case "start":
            # Start displaying the pattern sequence.
            lightcrafter.set_pattern_display_control(2)
        case "pause":
            # Pause displaying the pattern sequence.
            lightcrafter.set_pattern_display_control(1)
        case "stop":
            # Stop displaying the pattern sequence.
            lightcrafter.set_pattern_display_control(0)
        case "end":
            # End the experiment
            lightcrafter.set_pattern_display_control(0)
            break
        case other:
            print("Invalid pattern display action. Please try again.")

# Properly disconnects from the DLP LightCrafter 9000 EVM.
lightcrafter.disconnect()
