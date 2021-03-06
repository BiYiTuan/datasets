# coding=utf-8
# Copyright 2019 The TensorFlow Datasets Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for extractor."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from absl.testing import absltest
import tensorflow as tf
from tensorflow_datasets import testing
from tensorflow_datasets.core.download import extractor
from tensorflow_datasets.core.download import resource as resource_lib


def _read(path):
  with tf.io.gfile.GFile(path, 'rb') as f:
    return f.read()


class ExtractorTest(testing.TestCase):

  @classmethod
  def setUpClass(cls):
    super(ExtractorTest, cls).setUpClass()
    f1_path = os.path.join(cls.test_data, '6pixels.png')
    f2_path = os.path.join(cls.test_data, 'foo.csv')
    with tf.io.gfile.GFile(f1_path, 'rb') as f1_f:
      cls.f1_content = f1_f.read()
    with tf.io.gfile.GFile(f2_path, 'rb') as f2_f:
      cls.f2_content = f2_f.read()

  def setUp(self):
    super(ExtractorTest, self).setUp()
    self.extractor = extractor.get_extractor()
    self.extractor._pbar_path = absltest.mock.MagicMock()
    # Where archive will be extracted:
    self.to_path = os.path.join(self.tmp_dir, 'extracted_arch')
    # Obviously it must not exist before test runs:
    self.assertFalse(tf.io.gfile.exists(self.to_path))

    self.result_path = os.path.join(self.to_path, '6pixels.png')

  def test_unknown_method(self):
    with self.assertRaises(ValueError):
      resource = resource_lib.Resource(
          path='from/path',
          extract_method=resource_lib.ExtractMethod.NO_EXTRACT)
      self.extractor.extract(resource, 'to/path')

  def _test_extract(self, method, archive_name, expected_files):
    from_path = os.path.join(self.test_data, 'archives', archive_name)
    resource = resource_lib.Resource(path=from_path, extract_method=method)
    self.extractor.extract(resource, self.to_path).get()
    for name, content in expected_files.items():
      path = os.path.join(self.to_path, name)
      self.assertEqual(_read(path), content, 'File %s has bad content.' % path)

  def test_zip(self):
    self._test_extract(
        resource_lib.ExtractMethod.ZIP, 'arch1.zip',
        {'6pixels.png': self.f1_content, 'foo.csv': self.f2_content})

  def test_tar(self):
    self._test_extract(
        resource_lib.ExtractMethod.TAR, 'arch1.tar',
        {'6pixels.png': self.f1_content, 'foo.csv': self.f2_content})

  def test_targz(self):
    self._test_extract(
        resource_lib.ExtractMethod.TAR_GZ, 'arch1.tar.gz',
        {'6pixels.png': self.f1_content, 'foo.csv': self.f2_content})

  def test_gzip(self):
    from_path = os.path.join(self.test_data, 'archives', 'arch1.tar.gz')
    resource = resource_lib.Resource(
        path=from_path, extract_method=resource_lib.ExtractMethod.GZIP)
    self.extractor.extract(resource, self.to_path).get()
    arch1_path = os.path.join(self.test_data, 'archives', 'arch1.tar')
    self.assertEqual(_read(self.to_path), _read(arch1_path))

  def test_gzip2(self):
    # Same as previous test, except it is not a .tar.gz, but a .gz.
    from_path = os.path.join(self.test_data, 'archives', 'foo.csv.gz')
    resource = resource_lib.Resource(
        path=from_path, extract_method=resource_lib.ExtractMethod.GZIP)
    self.extractor.extract(resource, self.to_path).get()
    foo_csv_path = os.path.join(self.test_data, 'foo.csv')
    self.assertEqual(_read(self.to_path), _read(foo_csv_path))

  def test_absolute_path(self):
    from_path = os.path.join(self.test_data, 'archives', 'absolute_path.tar')
    resource = resource_lib.Resource(
        path=from_path, extract_method=resource_lib.ExtractMethod.TAR)
    promise = self.extractor.extract(resource, self.to_path)
    with self.assertRaisesWithPredicateMatch(
        extractor.ExtractError, 'is not safe'):
      promise.get()

  def test_wrong_method(self):
    from_path = os.path.join(self.test_data, 'archives', 'foo.csv.gz')
    resource = resource_lib.Resource(
        path=from_path, extract_method=resource_lib.ExtractMethod.ZIP,
        url='http://example.com/foo.zip')
    promise = self.extractor.extract(resource, self.to_path)
    expected_msg = (
        'foo.csv.gz (http://example.com/foo.zip): File is not a zip file.')
    with self.assertRaisesWithPredicateMatch(
        extractor.ExtractError, expected_msg):
      promise.get()


if __name__ == '__main__':
  testing.test_main()
