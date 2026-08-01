"""Tests for the codebook dataset format.

The compressed form only earns its place if it is *exactly* equal to the text
it replaces — a lossy encoding could silently flip a classification and quietly
change every number the app reports. These tests hold it to that.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from nnrepair.datasets import (
    CODEBOOK_SUFFIX,
    compress_dataset,
    iter_inputs,
    load_inputs,
    resolve_dataset,
)

ARTIFACT_ROOT = Path(__file__).resolve().parents[3] / "NNRepair"
MNIST_DATA = ARTIFACT_ROOT / "NN-Code" / "mnist0-adv" / "data"


def write_csv(path: Path, data: np.ndarray) -> Path:
    np.savetxt(path, data, delimiter=",", fmt="%.9f")
    return path


@pytest.fixture
def sample(tmp_path):
    """A small array with the shape of the real data: few distinct values."""
    rng = np.random.default_rng(11)
    # Mimic 8-bit pixels perturbed by a fixed epsilon, as FGSM produces.
    levels = np.round(np.arange(0, 256) / 255.0 + 0.05, 9)
    data = rng.choice(levels, size=(40, 784))
    return write_csv(tmp_path / "inputs.txt", data)


class TestCompression:
    def test_round_trip_is_exact(self, sample):
        compress_dataset(sample)
        reference = np.loadtxt(sample, delimiter=",", dtype=np.float64)
        np.testing.assert_array_equal(load_inputs(sample.with_suffix(CODEBOOK_SUFFIX)), reference)

    def test_output_is_substantially_smaller(self, sample):
        written = compress_dataset(sample)
        assert written.stat().st_size < sample.stat().st_size / 4

    def test_codes_are_uint16_and_values_float64(self, sample):
        written = compress_dataset(sample)
        with np.load(written) as archive:
            assert archive["codes"].dtype == np.uint16
            assert archive["values"].dtype == np.float64

    def test_refuses_data_with_too_many_distinct_values(self, tmp_path):
        rng = np.random.default_rng(3)
        crowded = write_csv(tmp_path / "crowded.txt", rng.uniform(size=(200, 400)))
        with pytest.raises(ValueError, match="too many"):
            compress_dataset(crowded)

    def test_missing_source(self, tmp_path):
        with pytest.raises(OSError):
            compress_dataset(tmp_path / "absent.txt")


class TestResolution:
    def test_prefers_the_compressed_sibling(self, sample):
        assert resolve_dataset(sample) == sample
        compress_dataset(sample)
        assert resolve_dataset(sample).suffix == CODEBOOK_SUFFIX

    def test_leaves_text_alone_when_no_sibling(self, sample):
        assert resolve_dataset(sample) == sample


class TestIteration:
    def test_both_forms_yield_identical_images(self, sample):
        shape = (28, 28, 1)
        from_text = list(iter_inputs(sample, shape, False))
        compress_dataset(sample)
        from_codebook = list(iter_inputs(sample, shape, False))

        assert len(from_text) == len(from_codebook) == 40
        for text_image, codebook_image in zip(from_text, from_codebook):
            np.testing.assert_array_equal(text_image, codebook_image)
            assert text_image.shape == shape

    def test_limit_applies_to_both_forms(self, sample):
        assert len(list(iter_inputs(sample, (28, 28, 1), False, limit=7))) == 7
        compress_dataset(sample)
        assert len(list(iter_inputs(sample, (28, 28, 1), False, limit=7))) == 7

    def test_normalisation_divides_by_255(self, sample):
        plain = next(iter_inputs(sample, (28, 28, 1), False))
        scaled = next(iter_inputs(sample, (28, 28, 1), True))
        np.testing.assert_allclose(scaled, plain / 255.0)

    def test_wrong_row_width_is_rejected(self, tmp_path):
        bad = write_csv(tmp_path / "bad.txt", np.zeros((3, 10)))
        with pytest.raises(ValueError, match="expected 784"):
            list(iter_inputs(bad, (28, 28, 1), False))


@pytest.mark.skipif(not MNIST_DATA.is_dir(), reason="MNIST datasets not present")
class TestAgainstShippedData:
    def test_first_rows_round_trip_exactly(self, tmp_path):
        """Compress a real slice and confirm it reproduces the text bit for bit."""
        source = MNIST_DATA / "mnist_test_csv_fgsm_epsilon0.05.txt"
        slice_path = tmp_path / source.name
        with source.open() as handle, slice_path.open("w") as out:
            for _ in range(200):
                out.write(handle.readline())

        compress_dataset(slice_path)
        reference = np.loadtxt(slice_path, delimiter=",", dtype=np.float64)
        np.testing.assert_array_equal(
            load_inputs(slice_path.with_suffix(CODEBOOK_SUFFIX)), reference
        )

    def test_real_data_has_few_distinct_values(self):
        """The premise of the codebook: 8-bit source, so the value set is tiny."""
        source = MNIST_DATA / "mnist_test_csv_fgsm_epsilon0.05.txt"
        sample = np.loadtxt(source, delimiter=",", dtype=np.float64, max_rows=200)
        assert np.unique(sample).size < 1000
