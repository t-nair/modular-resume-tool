"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check if we have a stored resume ID
    const resumeId = localStorage.getItem("resumeId");
    if (resumeId) {
      router.push("/dashboard");
    } else {
      router.push("/upload");
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <p className="text-gray-500">Redirecting...</p>
    </div>
  );
}
