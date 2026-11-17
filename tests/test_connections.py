# vim: set fileencoding=utf-8 :

import tempfile
import pytest

import pyvips
from helpers import JPEG_FILE, WEBP_FILE, temp_filename, skip_if_no


class TestConnections:
    @classmethod
    def setup_class(cls):
        cls.tempdir = tempfile.mkdtemp()

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_connection(self):
        source = pyvips.Source.new_from_file(JPEG_FILE)
        image = pyvips.Image.new_from_source(source, '', access='sequential')
        filename = temp_filename(self.tempdir, '.png')
        target = pyvips.Target.new_to_file(filename)
        image.write_to_target(target, '.png')

        image = pyvips.Image.new_from_file(JPEG_FILE, access='sequential')
        image2 = pyvips.Image.new_from_file(filename, access='sequential')

        assert (image - image2).abs().max() < 10

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_source_custom_no_seek(self):
        input_file = open(JPEG_FILE, "rb")

        def read_handler(size):
            return input_file.read(size)

        source = pyvips.SourceCustom()
        source.on_read(read_handler)

        image = pyvips.Image.new_from_source(source, '', access='sequential')
        image2 = pyvips.Image.new_from_file(JPEG_FILE, access='sequential')

        assert (image - image2).abs().max() == 0

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_source_custom(self):
        input_file = open(JPEG_FILE, "rb")

        def read_handler(size):
            return input_file.read(size)

        def seek_handler(offset, whence):
            input_file.seek(offset, whence)
            return input_file.tell()

        source = pyvips.SourceCustom()
        source.on_read(read_handler)
        source.on_seek(seek_handler)

        image = pyvips.Image.new_from_source(source, '',
                                             access='sequential')
        image2 = pyvips.Image.new_from_file(JPEG_FILE, access='sequential')

        assert (image - image2).abs().max() == 0

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_target_custom(self):
        filename = temp_filename(self.tempdir, '.png')
        output_file = open(filename, "w+b")

        def write_handler(chunk):
            return output_file.write(chunk)

        def end_handler():
            try:
                output_file.close()
            except IOError:
                return -1
            else:
                return 0

        target = pyvips.TargetCustom()
        target.on_write(write_handler)
        target.on_end(end_handler)

        image = pyvips.Image.new_from_file(JPEG_FILE, access='sequential')
        image.write_to_target(target, '.png')

        image = pyvips.Image.new_from_file(JPEG_FILE, access='sequential')
        image2 = pyvips.Image.new_from_file(filename, access='sequential')

        assert (image - image2).abs().max() == 0

    @skip_if_no('jpegload')
    @skip_if_no('tiffsave')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 13),
                        reason="requires libvips >= 8.13")
    def test_target_custom_seek(self):
        filename = temp_filename(self.tempdir, '.png')
        output_file = open(filename, "w+b")

        def write_handler(chunk):
            return output_file.write(chunk)

        def read_handler(size):
            return output_file.read(size)

        def seek_handler(offset, whence):
            output_file.seek(offset, whence)
            return output_file.tell()

        def end_handler():
            try:
                output_file.close()
            except IOError:
                return -1
            else:
                return 0

        target = pyvips.TargetCustom()
        target.on_write(write_handler)
        target.on_read(read_handler)
        target.on_seek(seek_handler)
        target.on_end(end_handler)

        image = pyvips.Image.new_from_file(JPEG_FILE, access='sequential')
        image.write_to_target(target, '.tif')

        image = pyvips.Image.new_from_file(JPEG_FILE, access='sequential')
        image2 = pyvips.Image.new_from_file(filename, access='sequential')

        assert (image - image2).abs().max() == 0

    # test webp as well, since that maps the stream rather than using read

    @skip_if_no('webpload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_source_custom_webp_no_seek(self):
        input_file = open(WEBP_FILE, "rb")

        def read_handler(size):
            return input_file.read(size)

        source = pyvips.SourceCustom()
        source.on_read(read_handler)

        image = pyvips.Image.new_from_source(source, '',
                                             access='sequential')
        image2 = pyvips.Image.new_from_file(WEBP_FILE, access='sequential')

        assert (image - image2).abs().max() == 0

    @skip_if_no('webpload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_source_custom_webp(self):
        input_file = open(WEBP_FILE, "rb")

        def read_handler(size):
            return input_file.read(size)

        def seek_handler(offset, whence):
            input_file.seek(offset, whence)
            return input_file.tell()

        source = pyvips.SourceCustom()
        source.on_read(read_handler)
        source.on_seek(seek_handler)

        image = pyvips.Image.new_from_source(source, '',
                                             access='sequential')
        image2 = pyvips.Image.new_from_file(WEBP_FILE, access='sequential')

        assert (image - image2).abs().max() == 0

    # exceptions raised by custom source/target callbacks must reach the
    # caller with their original type and message, and must not leave the
    # process unable to process the next image

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_source_custom_pixels_match_file(self):
        input_file = open(JPEG_FILE, "rb")

        def read_handler(size):
            return input_file.read(size)

        source = pyvips.SourceCustom()
        source.on_read(read_handler)

        image = pyvips.Image.new_from_source(source, '',
                                             access='sequential')
        image2 = pyvips.Image.new_from_file(JPEG_FILE, access='sequential')

        # every pixel of every band must be identical
        assert image.width == image2.width
        assert image.height == image2.height
        assert image.bands == image2.bands
        assert (image - image2).abs().max() == 0

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_source_custom_read_exception(self):
        input_file = open(JPEG_FILE, "rb")
        calls = {"n": 0}

        def read_handler(size):
            calls["n"] += 1
            if calls["n"] > 1:
                raise IOError("simulated 503")
            return input_file.read(size)

        source = pyvips.SourceCustom()
        source.on_read(read_handler)

        with pytest.raises(OSError, match="simulated 503"):
            pyvips.Image.new_from_source(source, '', access='sequential')

        # the failure must not poison later loads
        input_file2 = open(JPEG_FILE, "rb")

        def read_handler2(size):
            return input_file2.read(size)

        source2 = pyvips.SourceCustom()
        source2.on_read(read_handler2)

        image = pyvips.Image.new_from_source(source2, '',
                                             access='sequential')
        image2 = pyvips.Image.new_from_file(JPEG_FILE, access='sequential')

        assert (image - image2).abs().max() == 0

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_source_custom_read_exception_sniff(self):
        def read_handler(size):
            raise IOError("simulated 503")

        source = pyvips.SourceCustom()
        source.on_read(read_handler)

        with pytest.raises(OSError, match="simulated 503"):
            pyvips.Image.new_from_source(source, '', access='sequential')

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_source_custom_overread(self):
        def read_handler(size):
            return b'\x00' * (size + 1)

        source = pyvips.SourceCustom()
        source.on_read(read_handler)

        with pytest.raises(ValueError, match="but only"):
            pyvips.Image.new_from_source(source, '', access='sequential')

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_source_custom_seek_exception(self):
        input_file = open(JPEG_FILE, "rb")

        def read_handler(size):
            return input_file.read(size)

        def seek_handler(offset, whence):
            raise IOError("simulated 503")

        source = pyvips.SourceCustom()
        source.on_read(read_handler)
        source.on_seek(seek_handler)

        with pytest.raises(OSError, match="simulated 503"):
            pyvips.Image.new_from_source(source, '', access='random')

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_target_custom_write_exception(self):
        def write_handler(chunk):
            raise IOError("simulated 503")

        target = pyvips.TargetCustom()
        target.on_write(write_handler)

        image = pyvips.Image.new_from_file(JPEG_FILE)

        with pytest.raises(OSError, match="simulated 503"):
            image.write_to_target(target, '.png')

        # a good write must still work afterwards
        image.write_to_buffer('.png')

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_target_custom_write_invalid_length(self):
        image = pyvips.Image.new_from_file(JPEG_FILE)

        def write_long(chunk):
            return len(chunk) + 1

        target = pyvips.TargetCustom()
        target.on_write(write_long)

        with pytest.raises(ValueError, match="expected between"):
            image.write_to_target(target, '.png')

        def write_negative(chunk):
            return -1

        target = pyvips.TargetCustom()
        target.on_write(write_negative)

        with pytest.raises(ValueError, match="expected between"):
            image.write_to_target(target, '.png')

        def write_non_int(chunk):
            return "nope"

        target = pyvips.TargetCustom()
        target.on_write(write_non_int)

        with pytest.raises(TypeError, match="integer"):
            image.write_to_target(target, '.png')

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 9),
                        reason="requires libvips >= 8.9")
    def test_target_custom_end_exception(self):
        def write_handler(chunk):
            return len(chunk)

        def end_handler():
            raise IOError("shard not fully uploaded")

        target = pyvips.TargetCustom()
        target.on_write(write_handler)
        target.on_end(end_handler)

        image = pyvips.Image.new_from_file(JPEG_FILE)

        with pytest.raises(OSError, match="shard not fully uploaded"):
            image.write_to_target(target, '.png')

    @skip_if_no('jpegload')
    @pytest.mark.skipif(not pyvips.at_least_libvips(8, 13),
                        reason="requires libvips >= 8.13")
    def test_target_custom_end_error(self):
        def write_handler(chunk):
            return len(chunk)

        def end_handler():
            return -1

        target = pyvips.TargetCustom()
        target.on_write(write_handler)
        target.on_end(end_handler)

        image = pyvips.Image.new_from_file(JPEG_FILE)

        # on_end returning -1 must keep raising a libvips error
        with pytest.raises(pyvips.Error):
            image.write_to_target(target, '.png')
