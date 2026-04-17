import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { useAppDispatch, useAppSelector } from "@/store";
import { loginFailure, loginSuccess } from "@/store/slices/authSlice";

export const AuthContainer = () => {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const dispatch = useAppDispatch();
  const auth = useAppSelector((state) => state.auth);
  const navigate = useNavigate();

  const locked = auth.lockedUntil ? auth.lockedUntil > Date.now() : false;

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (locked) {
      return;
    }
    if (username === "admin" && password === "admin123") {
      dispatch(loginSuccess({ token: "demo-token", user: { username, role: "admin" } }));
      navigate("/admin");
    } else {
      dispatch(loginFailure());
    }
  };

  return (
    <Box sx={{ display: "grid", placeItems: "center", minHeight: "70vh" }}>
      <Paper sx={{ p: 3, width: "100%", maxWidth: 420 }} component="form" onSubmit={onSubmit}>
        <Stack spacing={2}>
          <Typography variant="h5">Admin Login</Typography>
          <TextField label="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {locked ? <Alert severity="error">Account temporarily locked after failed attempts.</Alert> : null}
          <Button type="submit" variant="contained" disabled={locked}>Sign in</Button>
        </Stack>
      </Paper>
    </Box>
  );
};
