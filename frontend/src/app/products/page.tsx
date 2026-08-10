"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FlaskConical, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CardGridSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { Product } from "@/lib/types";

export default function ProductsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", sku: "", category: "", allergens: "", description: "" });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const { data: products, isLoading } = useQuery({
    queryKey: ["products"],
    queryFn: async () => (await api.get<Product[]>("/products")).data,
  });

  async function createProduct(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post("/products", form);
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      setOpen(false);
      setForm({ name: "", sku: "", category: "", allergens: "", description: "" });
      toast.success("Product created.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <ProtectedShell title="Product Formulation">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-ink-500">
          Products and their versioned formulations — ingredient composition, cost, and allergen roll-up.
        </p>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> New Product
        </Button>
      </div>

      {isLoading ? (
        <CardGridSkeleton count={3} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products?.length === 0 && (
            <Card className="sm:col-span-2 lg:col-span-3">
              <CardContent className="p-0">
                <EmptyState
                  icon={FlaskConical}
                  title="No products yet"
                  description="Create one to start building a versioned formulation with cost and allergen roll-up."
                  action={{ label: "New Product", onClick: () => setOpen(true) }}
                />
              </CardContent>
            </Card>
          )}
          {products?.map((product) => (
            <Link key={product.id} href={`/products/${product.id}`}>
              <Card className="card-hover h-full">
                <CardContent>
                  <div className="mb-2 flex items-start justify-between">
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                      <FlaskConical className="h-4 w-4" />
                    </span>
                    {product.category && (
                      <span className="rounded-full bg-ink-100 px-2 py-0.5 text-xs text-ink-600">
                        {product.category}
                      </span>
                    )}
                  </div>
                  <p className="font-medium text-ink-900">{product.name}</p>
                  {product.sku && <p className="mt-0.5 text-xs text-ink-400">SKU: {product.sku}</p>}
                  <p className="mt-1 line-clamp-2 text-sm text-ink-500">
                    {product.description || "No description yet."}
                  </p>
                  {product.allergens && (
                    <p className="mt-2 text-xs font-medium text-amber-700">Allergens: {product.allergens}</p>
                  )}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} title="New Product" description="Add a product to start building its formulation.">
        <form onSubmit={createProduct} className="space-y-4">
          <div>
            <Label htmlFor="name">Product name</Label>
            <Input id="name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Peanut Butter Cookies" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="sku">SKU</Label>
              <Input id="sku" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} />
            </div>
            <div>
              <Label htmlFor="category">Category</Label>
              <Input id="category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="e.g. bakery" />
            </div>
          </div>
          <div>
            <Label htmlFor="allergens">Known allergens</Label>
            <Input id="allergens" value={form.allergens} onChange={(e) => setForm({ ...form, allergens: e.target.value })} placeholder="e.g. peanuts, milk, wheat" />
          </div>
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>{saving ? "Creating…" : "Create Product"}</Button>
          </div>
        </form>
      </Dialog>
    </ProtectedShell>
  );
}
