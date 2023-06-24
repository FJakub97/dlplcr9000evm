"""
copied from this repository
https://github.com/e841018/ERLE
@author Ashu
https://github.com/QI2lab/mcSIM/blob/master/mcsim/expt_ctrl/dlp6500.py
@author QI2lab
https://github.com/micropolimi/DMD_ScopeFoundry
@authour micropolimi
"""

# encode image of shape (n<=24, 1080, 1920) with Enhanced Run-Length Encoding (ERLE)
# described in http://www.ti.com/lit/pdf/dlpu018

import numpy as np
import struct
from typing import List

pack32be = struct.Struct(">I").pack  # uint32 big endian

WIDTH = int(2560 / 2)
HEIGHT = 1600


def get_header():
    """
    generate header defined in section 2.4.2
    """
    header = bytearray(0)
    # signature
    header += bytearray([0x53, 0x70, 0x6C, 0x64])
    # width
    header += bytearray([WIDTH % 256, WIDTH // 256])
    # height
    header += bytearray([HEIGHT % 256, HEIGHT // 256])
    # number of bytes, will be overwritten later
    header += bytearray(4)
    # reserved
    header += bytearray([0xFF] * 8)
    # background color (BB GG RR 00)
    header += bytearray(4)
    # reserved
    header.append(0)
    # compression, 0=Uncompressed, 1=RLE, 2=Enhanced RLE
    header.append(2)
    # reserved
    header.append(1)
    header += bytearray(21)
    return header


header_template = get_header()


# def merge(images):
#     '''
#     merge up to 24 binary images into a single 24-bit image, each pixel is an uint32 of format 0x00BBGGRR
#     '''
#     image32 = np.zeros((HEIGHT, WIDTH), dtype=np.uint32)
#     n_img = len(images)
#     batches = [8]*(n_img//8)
#     logger.debug(f'batches : {batches}')
#     if n_img % 8:
#         batches.append(n_img % 8)
#     for idx, batch_size in enumerate(batches):
#         image8 = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
#         for j in range(batch_size):
#             image8 += (images[idx*8+j]*(1 << j)).astype(np.uint8)

#         image32 += image8*(1 << (idx*8))
#         logger.debug(f'image32 | shape : {image32.shape} | dtype : {image32.dtype}')
#     return image32


# def bgr(pixel):
#     '''
#     convert an uint32 pixel into [B, G, R] bytes
#     '''
#     return pack32be(pixel)[1:4]


# def enc128(num):
#     '''
#     encode num (up to 32767) into 1 or 2 bytes
#     '''
#     return bytearray([(num & 0x7f) | 0x80, num >> 7]) if num >= 128 else bytearray([num])


# def run_len(row, idx):
#     '''
#     find the length of the longest run starting from idx in row
#     '''
#     stride = 128
#     length = len(row)
#     j = idx
#     while j < length and row[j]:
#         if j % stride == 0 and np.all(row[j:j+stride]):
#             j += min(stride, length-j)
#         else:
#             j += 1
#     return j-idx


# def encode_row(row, same_prev):
#     '''
#     encode a row of length 1920 with the format described in section 2.4.3.2
#     '''
#     # same_prev = np.zeros(1920, dtype=bool) if i==0 else image[i]==image[i-1]
#     # bool array indicating if same as next element, shape = (width - 1, )
#     same = np.logical_not(np.diff(row))
#     # same as previous row or same as next element, shape = (width -1 , )
#     same_either = np.logical_or(same_prev[:WIDTH-1], same)
#     logger.debug(f'same shape  [{same.shape}] | same prev shape [{same_prev.shape}]')

#     j = 0
#     compressed = bytearray(0)
#     while j < WIDTH*2:

#         # copy n pixels from previous line
#         if same_prev[j]:
#             r = run_len(same_prev, j+1) + 1
#             j += r
#             compressed += b'\x00\x01' + enc128(r)

#         # repeat single pixel n times
#         elif j < (WIDTH-1) and same[j]:
#             r = run_len(same, j+1) + 2
#             j += r
#             compressed += enc128(r) + bgr(row[j-1])

#         # single uncompressed pixel
#         elif j > (WIDTH-3) or same_either[j+1]:
#             compressed += b'\x01' + bgr(row[j])
#             j += 1

#         # multiple uncompressed pixels
#         else:
#             j_start = j
#             pixels = bgr(row[j]) + bgr(row[j+1])
#             j += 2
#             while j == (WIDTH-1) or not same_either[j]:
#                 pixels += bgr(row[j])
#                 j += 1
#             compressed += b'\x00' + enc128(j-j_start) + pixels

#     return compressed + b'\x00\x00'

# def encode(images):
#     '''
#     encode image with the format described in section 2.4.3.2.1
#     '''
#     # header
#     encoded = bytearray(header_template)

#     # uint32 array, shape = (1080, 1920)
#     image = merge(images)

#     # image content
#     for i in range(HEIGHT):
#         # bool array indicating if same as previous row, shape = (1920, )
#         same_prev = np.zeros(WIDTH, dtype=bool) if i == 0 else image[i] == image[i-1]
#         encoded += encode_row(image[i], same_prev)

#     # end of image
#     encoded += b'\x00\x01\x00'

#     # pad to 4-byte boundary
#     encoded += bytearray((-len(encoded)) % 4)

#     # overwrite number of bytes in header
#     # uint32 little endian, offset=8
#     struct.pack_into('<I', encoded, 8, len(encoded))

#     return encoded, len(encoded)

# def convlen(num: int,length: int) -> str:
#     '''
#     converts a number into a bit string of given length

#     Input args:
#         num: int
#             number to be converted
#         length: int
#             length of output string

#     Return:
#         bin_num: str
#             bit string
#     '''
#     bin_num=bin(num)[2:]
#     padding=length-len(bin_num)
#     bin_num='0'*padding+bin_num
#     return bin_num

# def bitstobytes(num: str) -> List[int]:
#     '''
#     converts a bit string into a given number of bytes

#     Input args:
#         num: str
#             number to be converted ex) '0001'

#     Return:
#         bytelist: List[int]
#             converted byte string in list. each number in the list is of 1 byte
#             ex) [1, 0] when input is '0001'
#     '''
#     bytelist=[]
#     if len(num)%8!=0:
#         padding=8-len(num)%8
#         num='0'*padding+num
#     for i in range(len(num)//8):
#         bytelist.append(int(num[8*i:8*(i+1)],2))

#     bytelist.reverse() # [MSB, LSB] -> [LSB, MSB]
#     return bytelist


def encode_erle(pattern):
    """
    I copied this code from
    https://github.com/QI2lab/mcSIM/blob/master/mcsim/expt_ctrl/dlp6500.py
    Encode a 24bit pattern in enhanced run length encoding (ERLE).
    ERLE is similar to RLE, but now the number of repeats byte is given by either one or two bytes.
    specification:
    ctrl byte 1, ctrl byte 2, ctrl byte 3, description
    0          , 0          , n/a        , end of image
    0          , 1          , n          , copy n pixels from the same position on the previous line
    0          , n>1        , n/a        , n uncompressed RGB pixels follow
    n>1        , n/a        , n/a        , repeat following pixel n times
    :param pattern: uint8 3 x Ny x Nx array of RGB values, or Ny x Nx array
    :return pattern_compressed:
    """

    pattern = np.moveaxis(pattern, [0, 1, 2], [1, 2, 0])

    # pattern must be uint8
    if pattern.dtype != np.uint8:
        raise ValueError("pattern must be of type uint8")

    # if 2D pattern, expand this to RGB with pattern in B layer and RG=0
    if pattern.ndim == 2:
        pattern = np.concatenate(
            (
                np.zeros((1,) + pattern.shape, dtype=np.uint8),
                np.zeros((1,) + pattern.shape, dtype=np.uint8),
                np.array(pattern[None, :, :], copy=True),
            ),
            axis=0,
        )

    if pattern.ndim != 3 and pattern.shape[0] != 3:
        raise ValueError("Image data is wrong shape. Must be 3 x ny x nx, with RGB values in each layer.")

    pattern_compressed = []
    _, ny, nx = pattern.shape

    # todo: not sure if this is allowed to cross row_rgb boundaries? If so, could pattern.ravel() instead of looping
    # todo: don't think above suggestion works, but if last n pixels of above row_rgb are same as first n of this one
    # todo: then with ERLE encoding I can use \x00\x01 Hex(n). But checking this may not be so easy. Right now
    # todo: only implemented if entire rows are the same!
    # todo: erle and rle are different enough probably should split apart more
    # loop over pattern rows
    for ii in range(pattern.shape[1]):
        row_rgb = pattern[:, ii, :]

        # if this row_rgb is the same as the last row_rgb, can communicate this by sending length of row_rgb
        # and then \x00\x01 (copy n pixels from previous line)
        # todo: can also do this for shorter sequences than the entire row_rgb
        if ii > 0 and np.array_equal(row_rgb, pattern[:, ii - 1, :]):
            msb, lsb = erle_len2bytes(nx)
            pattern_compressed += [0x00, 0x01, msb, lsb]
        else:
            # find points along row where pixel value changes
            # for RGB image, change happens when ANY pixel value changes
            value_changed = np.sum(np.abs(np.diff(row_rgb, axis=1)), axis=0) != 0
            # also need to include zero, as this will need to be encoded.
            # add one to index to get position of first new value instead of last old value
            inds_change = np.concatenate((np.array([0]), np.where(value_changed)[0] + 1))

            # get lengths for each repeat, including last one which extends until end of the line
            run_lens = np.concatenate((np.array(inds_change[1:] - inds_change[:-1]), np.array([nx - inds_change[-1]])))

            # now build compressed list
            for ii, rlen in zip(inds_change, run_lens):
                v = row_rgb[:, ii]
                length_bytes = erle_len2bytes(rlen)
                pattern_compressed += length_bytes + [v[0], v[1], v[2]]

    # bytes indicating image end
    pattern_compressed += [0x00, 0x01, 0x00]

    # get the header
    # Note: taken directly from sniffer of the TI GUI
    signature_bytes = [0x53, 0x70, 0x6C, 0x64]
    width_byte = list(struct.unpack("BB", struct.pack("<H", WIDTH)))
    height_byte = list(struct.unpack("BB", struct.pack("<H", HEIGHT)))
    # Number of bytes in encoded image_data
    num_encoded_bytes = list(struct.unpack("BBBB", struct.pack("<I", len(pattern_compressed))))
    reserved_bytes = [0xFF] * 8  # reserved
    bg_color_bytes = [0x00] * 4  # BG color BB, GG, RR, 00

    # # encoding 0 none, 1 rle, 2 erle
    # if compression_mode == 'none':
    #     encoding_byte = [0x00]
    # elif compression_mode == 'rle':
    #     encoding_byte = [0x01]
    # elif compression_mode == 'erle':
    #     encoding_byte = [0x02]
    # else:
    #     raise ValueError("compression_mode must be 'none', 'rle', or 'erle' but was '%s'" % compression_mode)

    encoding_byte = [0x02]  # 'erle' encoding
    general_data = (
        signature_bytes
        + width_byte
        + height_byte
        + num_encoded_bytes
        + reserved_bytes
        + bg_color_bytes
        + [0x00]
        + encoding_byte
        + [0x01]
        + [0x00] * 21
    )  # reserved

    data = general_data + pattern_compressed
    return data


def erle_len2bytes(length):
    """
    Encode a length between 0-2**15-1 as 1 or 2 bytes for use in erle encoding format.
    Do this in the following way: if length < 128, encode as one byte
    If length > 128, then encode as two bits. Create the least significant byte (LSB) as follows: set the most
    significant bit as 1 (this is a flag indicating two bytes are being used), then use the least signifcant 7 bits
    from length. Construct the most significant byte (MSB) by throwing away the 7 bits already encoded in the LSB.
    i.e.
    lsb = (length & 0x7F) | 0x80
    msb = length >> 7
    :param length: integer 0-(2**15-1)
    :return:
    """

    # check input
    if isinstance(length, float):
        if length.is_integer():
            length = int(length)
        else:
            raise TypeError("length must be convertible to integer.")

    # if not isinstance(length, int):
    #     raise Exception('length must be an integer')

    if length < 0 or length > 2**15 - 1:
        raise ValueError("length is negative or too large to be encoded.")

    # main function
    if length < 128:
        len_bytes = [length]
    else:
        # i.e. lsb is formed by taking the 7 least significant bits and extending to 8 bits by adding
        # a 1 in the msb position
        lsb = (length & 0x7F) | 0x80
        # second byte obtained by throwing away first 7 bits and keeping what remains
        msb = length >> 7
        len_bytes = [lsb, msb]

    return len_bytes


def erle_bytes2len(byte_list):
    """
    Convert a 1 or 2 byte list in little endian order to length
    :param list byte_list: [byte] or [lsb, msb]
    :return length:
    """
    # if msb is None:
    #     length = lsb
    # else:
    #     length = (msb << 7) + (lsb - 0x80)
    if len(byte_list) == 1:
        length = byte_list[0]
    else:
        lsb, msb = byte_list
        length = (msb << 7) + (lsb - 0x80)

    return
