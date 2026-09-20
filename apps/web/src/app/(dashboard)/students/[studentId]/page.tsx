"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  FileCheck2,
  GraduationCap,
  Loader2,
  Send,
  UserRound,
  Users,
  XCircle,
} from "lucide-react";

import {
  useApproveStudent,
  useExitStudent,
  useGraduateStudent,
  useReadyStudent,
  useStudent,
  useStudentDocuments,
  useStudentGuardians,
  useSubmitStudent,
  useVerifyDocument,
  useRejectDocument,
} from "@/hooks/use-students";

import { StudentStatus } from "@/components/students/student-status";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function ActionButton({
  label,
  icon: Icon,
  loading,
  disabled,
  onClick,
}: {
  label: string;
  icon: typeof Send;
  loading: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <Button
      type="button"
      disabled={disabled || loading}
      onClick={onClick}
      className="rounded-xl bg-[#27348B] hover:bg-[#202c78]"
    >
      {loading ? (
        <Loader2 className="mr-2 size-4 animate-spin" />
      ) : (
        <Icon className="mr-2 size-4" />
      )}
      {label}
    </Button>
  );
}

export default function StudentDetailPage() {
  const params = useParams<{
    studentId: string;
  }>();

  const studentId = params.studentId;

  const student =
    useStudent(studentId);

  const guardians =
    useStudentGuardians(studentId);

  const documents =
    useStudentDocuments(studentId);

  const submit =
    useSubmitStudent(studentId);

  const ready =
    useReadyStudent(studentId);

  const approve =
    useApproveStudent(studentId);

  const exit =
    useExitStudent(studentId);

  const graduate =
    useGraduateStudent(studentId);

  const verify =
    useVerifyDocument(studentId);

  const reject =
    useRejectDocument(studentId);

  const [exitDate, setExitDate] =
    useState(
      new Date()
        .toISOString()
        .slice(0, 10),
    );

  if (student.isLoading) {
    return (
      <div className="flex min-h-[500px] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-[#27348B]" />
      </div>
    );
  }

  if (
    student.isError ||
    !student.data
  ) {
    return (
      <div className="mx-auto max-w-4xl rounded-3xl border border-red-100 bg-red-50 p-10 text-center">
        <XCircle className="mx-auto size-10 text-red-500" />
        <h1 className="mt-4 text-xl font-bold text-red-800">
          Student could not be loaded
        </h1>
        <p className="mt-2 text-sm text-red-600">
          {student.error instanceof Error
            ? student.error.message
            : "The student API request failed."}
        </p>
        <Link
          href="/students"
          className="mt-6 inline-flex rounded-xl bg-[#27348B] px-4 py-2.5 text-sm font-bold text-white"
        >
          Back to students
        </Link>
      </div>
    );
  }

  const record = student.data;

  const fullName = [
    record.first_name,
    record.middle_name,
    record.last_name,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="mx-auto max-w-[1500px]">
      <div className="mb-6">
        <Link
          href="/students"
          className="inline-flex items-center gap-2 text-xs font-bold text-[#27348B]"
        >
          <ArrowLeft className="size-4" />
          Back to students
        </Link>
      </div>

      <Card className="overflow-hidden border-white/50 bg-white/70 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
        <div className="bg-[#27348B] p-6 text-white sm:p-8">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex size-16 shrink-0 items-center justify-center rounded-2xl bg-white/15 text-2xl font-black ring-1 ring-white/20">
                {record.first_name
                  ?.charAt(0)
                  .toUpperCase()}
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.15em] text-white/55">
                  Student profile
                </p>

                <h1 className="mt-1 text-2xl font-black">
                  {fullName}
                </h1>

                <p className="mt-1 text-xs text-white/60">
                  ID: {record.student_id}
                </p>
              </div>
            </div>

            <StudentStatus
              status={record.status}
            />
          </div>
        </div>

        <CardContent className="p-6">
          <div className="flex flex-wrap gap-2">
            {record.status ===
              "APPLICATION_DRAFT" && (
              <ActionButton
                label="Submit application"
                icon={Send}
                loading={
                  submit.isPending
                }
                onClick={() =>
                  submit.mutate()
                }
              />
            )}

            {record.status ===
              "SUBMITTED" && (
              <ActionButton
                label="Ready for approval"
                icon={FileCheck2}
                loading={
                  ready.isPending
                }
                onClick={() =>
                  ready.mutate()
                }
              />
            )}

            {record.status ===
              "READY_FOR_APPROVAL" && (
              <ActionButton
                label="Approve student"
                icon={CheckCircle2}
                loading={
                  approve.isPending
                }
                onClick={() =>
                  approve.mutate()
                }
              />
            )}

            {[
              "ACTIVE",
              "READY_FOR_APPROVAL",
            ].includes(
              record.status,
            ) && (
              <>
                <ActionButton
                  label="Graduate"
                  icon={GraduationCap}
                  loading={
                    graduate.isPending
                  }
                  onClick={() =>
                    graduate.mutate(
                      exitDate,
                    )
                  }
                />

                <ActionButton
                  label="Exit"
                  icon={XCircle}
                  loading={exit.isPending}
                  onClick={() =>
                    exit.mutate(
                      exitDate,
                    )
                  }
                />
              </>
            )}
          </div>

          {[
            "ACTIVE",
            "READY_FOR_APPROVAL",
          ].includes(
            record.status,
          ) && (
            <div className="mt-4 max-w-xs">
              <label className="mb-1.5 block text-xs font-semibold text-slate-500">
                Lifecycle date
              </label>

              <Input
                type="date"
                value={exitDate}
                onChange={(event) =>
                  setExitDate(
                    event.target.value,
                  )
                }
                className="rounded-xl"
              />
            </div>
          )}
        </CardContent>
      </Card>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <UserRound className="size-4 text-[#27348B]" />
              Personal information
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            {[
              [
                "Date of birth",
                record.date_of_birth ||
                  "Not provided",
              ],
              [
                "Gender",
                record.gender ||
                  "Not provided",
              ],
              [
                "Phone",
                record.phone ||
                  "Not provided",
              ],
              [
                "Email",
                record.email ||
                  "Not provided",
              ],
              [
                "Address",
                record.address ||
                  "Not provided",
              ],
            ].map(
              ([label, value]) => (
                <div key={label}>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    {label}
                  </p>
                  <p className="mt-1 text-sm font-medium text-slate-700">
                    {value}
                  </p>
                </div>
              ),
            )}
          </CardContent>
        </Card>

        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Users className="size-4 text-[#27348B]" />
              Guardians
            </CardTitle>
          </CardHeader>

          <CardContent>
            {guardians.isLoading ? (
              <p className="text-sm text-slate-400">
                Loading guardians...
              </p>
            ) : guardians.data?.length ? (
              <div className="space-y-3">
                {guardians.data.map(
                  (guardian) => (
                    <div
                      key={guardian.id}
                      className="rounded-2xl border border-slate-100 bg-white/70 p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold text-slate-800">
                          {
                            guardian.full_name
                          }
                        </p>

                        {guardian.is_primary && (
                          <span className="rounded-full bg-[#27348B]/10 px-2 py-1 text-[10px] font-bold text-[#27348B]">
                            Primary
                          </span>
                        )}
                      </div>

                      <p className="mt-1 text-xs text-slate-500">
                        {guardian.relationship}
                      </p>

                      <p className="mt-2 text-xs text-slate-500">
                        {guardian.phone ||
                          guardian.email ||
                          "No contact details"}
                      </p>
                    </div>
                  ),
                )}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center">
                <p className="text-sm font-medium text-slate-600">
                  No guardians recorded
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <GraduationCap className="size-4 text-[#27348B]" />
              Enrollment
            </CardTitle>
          </CardHeader>

          <CardContent>
            {record.enrollment ? (
              <div className="space-y-4">
                {[
                  [
                    "Enrollment date",
                    record.enrollment
                      .enrollment_date,
                  ],
                  [
                    "Status",
                    record.enrollment
                      .status,
                  ],
                  [
                    "School",
                    record.enrollment
                      .school_id,
                  ],
                  [
                    "Class",
                    record.enrollment
                      .class_id,
                  ],
                ].map(
                  ([label, value]) => (
                    <div key={label}>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        {label}
                      </p>
                      <p className="mt-1 break-all text-sm font-medium text-slate-700">
                        {value}
                      </p>
                    </div>
                  ),
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-400">
                No active enrollment.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6 border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <FileCheck2 className="size-4 text-[#27348B]" />
            Document verification
          </CardTitle>
        </CardHeader>

        <CardContent>
          {documents.isLoading ? (
            <p className="text-sm text-slate-400">
              Loading documents...
            </p>
          ) : documents.data?.length ? (
            <div className="space-y-3">
              {documents.data.map(
                (document) => (
                  <div
                    key={document.id}
                    className="flex flex-col gap-4 rounded-2xl border border-slate-100 bg-white/70 p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="font-semibold text-slate-800">
                        {
                          document.document_type
                        }
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        {document.file_name ||
                          "Document"}
                      </p>

                      <span className="mt-2 inline-flex rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-600">
                        {document.status}
                      </span>

                      {document.rejection_reason && (
                        <p className="mt-2 text-xs text-red-600">
                          {
                            document.rejection_reason
                          }
                        </p>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {[
                        "PENDING",
                        "REJECTED",
                      ].includes(
                        document.status,
                      ) && (
                        <Button
                          type="button"
                          size="sm"
                          disabled={
                            verify.isPending
                          }
                          onClick={() =>
                            verify.mutate(
                              {
                                documentId:
                                  document.id,
                              },
                            )
                          }
                          className="rounded-xl bg-emerald-600 hover:bg-emerald-700"
                        >
                          Verify
                        </Button>
                      )}

                      {[
                        "PENDING",
                        "VERIFIED",
                      ].includes(
                        document.status,
                      ) && (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={
                            reject.isPending
                          }
                          onClick={() => {
                            const reason =
                              window.prompt(
                                "Reason for rejection",
                              );

                            if (
                              reason?.trim()
                            ) {
                              reject.mutate(
                                {
                                  documentId:
                                    document.id,
                                  reason:
                                    reason.trim(),
                                },
                              );
                            }
                          }}
                          className="rounded-xl border-red-200 text-red-600 hover:bg-red-50"
                        >
                          Reject
                        </Button>
                      )}
                    </div>
                  </div>
                ),
              )}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-amber-200 bg-amber-50 p-6">
              <p className="font-semibold text-amber-800">
                No documents uploaded
              </p>

              <p className="mt-1 text-xs text-amber-700">
                The backend requires at least one
                document before the student can enter
                the approval stage.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}