// import axios from "axios";

// const client = axios.create({
//   baseURL: "/",
//   headers: { "Content-Type": "application/json" },
//   timeout: 60000
// });

// export async function scrapeUrl(url) {
//   const resp = await client.post("/scrape", { url });
//   return resp.data.result;
// }



import axios from "axios";

const client = axios.create({
  baseURL: "/",
  headers: { "Content-Type": "application/json" },
  timeout: 60000,
});

export async function scrapeUrl(url) {
  const payload = {
    url,
    mode: "dynamic",  
    scrolls: 3,           
    clicks: 5,            
    pagination_limit: 3   
  };

  console.log("Sending payload:", payload);

  const resp = await client.post("/scrape", payload);
  return resp.data.result;
}
