def deserialize_number(numpy_array):
    """
    Return single value arrays as a scalar.
    :param numpy_array: Numpy array containing a number to deserialize.
    :return: Array or scalar, based on array size.
    """
    if numpy_array is None:
        return numpy_array

    if len(numpy_array) == 1:
        return numpy_array[0]
    else:
        return numpy_array


def deserialize_string(numpy_array):
    """
    Return string that is serialized as a numpy array.
    :param numpy_array: Array to deserialize (UTF-8 is assumed)
    :return: String.
    """
    return numpy_array.tobytes().decode()


channel_type_deserializer_mapping = {
    # Default value if no channel_type specified.
    None: ("f8", deserialize_number),
    'int8': ('i1', deserialize_number),
    'uint8': ('u1', deserialize_number),
    'int16': ('i2', deserialize_number),
    'uint16': ('u2', deserialize_number),
    'int32': ('i4', deserialize_number),
    'uint32': ('u4', deserialize_number),
    'int64': ('i8', deserialize_number),
    'uint64': ('u8', deserialize_number),
    'float32': ('f4', deserialize_number),
    'float64': ('f8', deserialize_number),
    'string': ('u1', deserialize_string),
    'bool': ('u1', deserialize_number)
}