import "./globals.css";

export const metadata = {
  title: "MOMent AI | Your family, thoughtfully organised",
  description: "A calmer way to remember the little and important things for your family.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
