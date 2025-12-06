import axios from "axios";

const client = axios.create({
  baseURL: "/",
  headers: { "Content-Type": "application/json" },
  timeout: 60000
});

export async function scrapeUrl(url) {
  const resp = await client.post("/scrape", { url });
  return resp.data.result;
}
