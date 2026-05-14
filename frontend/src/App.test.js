import { render, screen } from "@testing-library/react";
import App from "./App";

beforeEach(() => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: false,
    status: 401,
  });
});

afterEach(() => {
  jest.resetAllMocks();
});

test("renders CricCircle landing page", async () => {
  render(<App />);
  expect(
    await screen.findByText(/Where cricket analysts earn trust, not just attention/i)
  ).toBeInTheDocument();
});
