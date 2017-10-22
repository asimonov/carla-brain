import numpy as np

class TLLabelConverter:
  """Helper class for converting between 'string', 'integer' and one-hot vector
  representation of labels

  Can be used standalone, but is used inside TLClassifierCNN as well for
  returning predictions.

  Examples:
    x, y = load_tl_extracts(data_dirs, desired_dim)
    # y here are strings like 'green' etc
    # filter data with only labels relevant for us
    converter = TLLabelConverter()
    x, y = converter.filter(x, y)

  Attributes:
    _relevant_labels: string array, full list of string labels we deal with.
                      Update as needed
  """
  def __init__(self):
    self._relevant_labels = ['off','green','yellow','red']
    self._n_classes = len(self._relevant_labels)
    self._label_to_i_dict = {}
    self._i_to_label_dict = {}
    self._label_to_oh_dict = {}
    for i, l in enumerate(self._relevant_labels):
      self._label_to_i_dict[l] = i
      self._i_to_label_dict[i] = l
      self._label_to_oh_dict[l] = [1 if x==i else 0 for x in range(self._n_classes)]

  def labels(self):
    """list of all labels
    Returns:
      :return: array of strings
    """
    return  self._relevant_labels

  def get_i(self, l):
    """return integer label id corresponding to string label
    Args:
      :param l: string label
    Returns:
      :return: integer
    """
    return self._label_to_i_dict[l]

  def get_l(self, i):
    """return string label corresponding to integer id
    Args:
      :param i: integer label id
    Returns:
      :return: string label
    """
    return self._i_to_label_dict[i]

  def get_oh(self, l):
    """return one-hot encoded vector corresponding to string label
    Args:
      :param l: string label
    Returns:
      :return: list/vector encoding label in one-hot fashion
    """
    return self._label_to_oh_dict[l]

  def filter(self, images, labels):
    """filter only examples with labels we know about
    Args:
      :param images: numpy array of images
      :param labels: numpy array of strings
    Returns:
      :return: images and labels arrays which are subsets of inputs, but only where labels are
               in `_relevant_labels`
    """
    x = images[np.isin(labels, self._relevant_labels)]
    y = labels[np.isin(labels, self._relevant_labels)]
    return x, y

  def convert_to_oh(self, labels):
    """convert list of string labels to corresponding one-hot-encoded representations
    Args:
      :param labels: list (or numpy array) of string labels
    Returns:
      :return: numpy array of one-hot encodings
    """
    return np.array([self._label_to_oh_dict[l] for l in labels])

  def convert_to_labels(self, classes):
    """convert list/numpy array of integer class id to corresponding string labels
    Args:
      :param classes: list (or numpy array) of label IDs
    Returns:
      :return: numpy array of string labels
    """
    return np.array([self._i_to_label_dict[i] for i in classes])

  def get_shape(self):
    """number of classification labels
    Returns:
      :return: tuple with number of classes
    """
    return (self._n_classes,)
