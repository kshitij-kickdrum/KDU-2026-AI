import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { ImageApiResponse } from '../../types';

interface ImageState {
  isOpen: boolean;
  result: ImageApiResponse | null;
  uploadedFileName: string | null;
}

const initialState: ImageState = {
  isOpen: false,
  result: null,
  uploadedFileName: null,
};

const imageSlice = createSlice({
  name: 'image',
  initialState,
  reducers: {
    setImageResult(state, action: PayloadAction<ImageApiResponse>) {
      state.result = action.payload;
      state.isOpen = true;
    },
    setUploadedFileName(state, action: PayloadAction<string | null>) {
      state.uploadedFileName = action.payload;
    },
    closePanel(state) {
      state.isOpen = false;
    },
    clearImageState(state) {
      state.isOpen = false;
      state.result = null;
      state.uploadedFileName = null;
    },
  },
});

export const { setImageResult, setUploadedFileName, closePanel, clearImageState } =
  imageSlice.actions;

export default imageSlice.reducer;
